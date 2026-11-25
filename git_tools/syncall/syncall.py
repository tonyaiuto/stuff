#!/usr/bin/env python3
"""Merge the repo's main line into every local branch.

See requirements.md for the intended behavior.

  syncall.py            sync all branches
  syncall.py .          resume: sync the branches after the current one
  syncall.py BRANCH     resume: sync the branches after BRANCH
  syncall.py --exclude 'wip/*'   extra exclusion patterns for this run

Exclusions come from `git config syncall.exclude` (multi-valued globs).
"""

import argparse
import fnmatch
import os
import subprocess
import sys

GIT = '/usr/bin/git'
# In order of preference, most preferred first.
MAIN_CANDIDATES = ['main', 'master', 'work', 'trunk']
IN_PROGRESS = ['MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD',
               'rebase-merge', 'rebase-apply']


class GitError(Exception):
  pass


def git(*args, cwd=None, check=True):
  """Run git, return stripped stdout. Raises GitError on failure if check."""
  p = subprocess.run([GIT] + list(args), cwd=cwd, text=True,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  if check and p.returncode != 0:
    raise GitError('git %s: %s' % (' '.join(args), p.stderr.strip()))
  return p.stdout.strip() if check else p


def git_ok(*args, cwd=None):
  return git(*args, cwd=cwd, check=False).returncode == 0


def local_branches():
  out = git('for-each-ref', '--format=%(refname:short)', 'refs/heads')
  return sorted(out.splitlines())


def choose_main(branches):
  for cand in MAIN_CANDIDATES:
    if cand in branches:
      return cand
  return 'main'


def worktree_map():
  """branch name -> worktree path, for every branch checked out somewhere."""
  result = {}
  path = None
  for line in git('worktree', 'list', '--porcelain').splitlines():
    if line.startswith('worktree '):
      path = line[len('worktree '):]
    elif line.startswith('branch refs/heads/'):
      result[line[len('branch refs/heads/'):]] = path
  return result


def dirty_reason(path):
  """Why we must not touch this checkout, or None if it is clean."""
  for name in IN_PROGRESS:
    p = git('rev-parse', '--git-path', name, cwd=path)
    if os.path.exists(os.path.join(path, p)):
      return '%s in progress' % name
  if git('status', '--porcelain', '--untracked-files=no', cwd=path):
    return 'uncommitted changes'
  return None


def configured_exclusions():
  p = git('config', '--get-all', 'syncall.exclude', check=False)
  return p.stdout.split() if p.returncode == 0 else []


def contains(branch, base, cwd=None):
  return git_ok('merge-base', '--is-ancestor', base, branch, cwd=cwd)


def die(msg):
  print('\nSTOPPED: %s' % msg, file=sys.stderr)
  sys.exit(1)


def source_remote(main_branch):
  """The remote that is the source of truth for the main line, or None."""
  remotes = git('remote').split()
  p = git('config', 'syncall.mainRemote', check=False)
  configured = p.stdout.strip() if p.returncode == 0 else ''
  if configured:
    if configured not in remotes:
      die('syncall.mainRemote is "%s", but there is no such remote' % configured)
    return configured
  if 'upstream' in remotes:
    return 'upstream'
  p = git('config', 'branch.%s.remote' % main_branch, check=False)
  tracking = p.stdout.strip() if p.returncode == 0 else ''
  if tracking in remotes:
    return tracking
  return remotes[0] if len(remotes) == 1 else None


def refresh_main(main_branch, here):
  """Fetch all remotes, then fast-forward local main to the source remote's.

  Never pushes, never rebases or merges: if local main has commits of its own
  we stop and explain.
  """
  print('== Fetching all')
  # Let git's own output through so the user can see what happened.
  if subprocess.run([GIT, 'fetch', '--all'], cwd=here).returncode != 0:
    die('git fetch --all failed')

  remote = source_remote(main_branch)
  if remote is None:
    print('== No remote to update %s from; leaving it as is' % main_branch)
    return
  ref = '%s/%s' % (remote, main_branch)
  if not git_ok('rev-parse', '--verify', '--quiet', ref, cwd=here):
    die('%s does not exist, so %s cannot be updated from %s.\n'
        'Set the remote with: git config syncall.mainRemote <remote>'
        % (ref, main_branch, remote))

  if not contains(ref, main_branch, cwd=here):
    own = git('log', '--oneline', '--max-count=10', '%s..%s' % (ref, main_branch),
              cwd=here)
    n = git('rev-list', '--count', '%s..%s' % (ref, main_branch), cwd=here)
    die('local %s has %s commit(s) that are not in %s, so it will not be '
        'updated.\nsyncall only fast-forwards the main line; it never '
        'merges or rebases it.\nCommits only on local %s%s:\n%s\n'
        'Move them to a branch, or reset %s, then run syncall again.'
        % (main_branch, n, ref, main_branch,
           ' (first 10)' if int(n) > 10 else '',
           '\n'.join('  ' + l for l in own.splitlines()), main_branch))

  if git('rev-parse', main_branch, cwd=here) == git('rev-parse', ref, cwd=here):
    print('== %s is up to date with %s' % (main_branch, ref))
    return
  print('== Fast-forwarding %s to %s' % (main_branch, ref))
  if subprocess.run([GIT, 'merge', '--ff-only', ref], cwd=here).returncode != 0:
    die('could not fast-forward %s to %s (uncommitted changes in the way?)'
        % (main_branch, ref))


def resume_hint(branch):
  return 'resolve, commit, then run: syncall.py .   (or: syncall.py %s)' % branch


def main():
  ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
  ap.add_argument('resume', nargs='?', metavar='. | BRANCH',
                  help='skip everything up to and including this branch')
  ap.add_argument('--exclude', action='append', default=[], metavar='GLOB',
                  help='also exclude branches matching GLOB (repeatable)')
  args = ap.parse_args()
  # Keep our output in order with the git subprocesses' output.
  sys.stdout.reconfigure(line_buffering=True)

  here = os.getcwd()
  try:
    here = git('rev-parse', '--show-toplevel')
  except GitError as e:
    sys.exit(str(e))

  branches = local_branches()
  main_branch = choose_main(branches)
  cur = git('branch', '--show-current', cwd=here)
  start = cur or git('rev-parse', 'HEAD', cwd=here)  # detached: restore by sha

  print('MAIN=%s' % main_branch)

  # R1: refresh the main line, only when run from main.
  if cur == main_branch:
    refresh_main(main_branch, here)

  # R4: resume. Position is computed over all branches, before exclusions.
  after = args.resume
  if after == '.':
    if not cur:
      sys.exit('"." needs a branch checked out here')
    after = cur
    reason = next((n for n in IN_PROGRESS
                   if os.path.exists(os.path.join(
                       here, git('rev-parse', '--git-path', n, cwd=here)))),
                  None)
    if reason:
      sys.exit('%s: %s; finish it first' % (cur, reason))
    if not contains(cur, main_branch, cwd=here):
      sys.exit('%s does not contain %s yet; finish its merge first'
               % (cur, main_branch))
  if after is not None:
    if after not in branches:
      sys.exit('no such branch: %s' % after)
    branches = branches[branches.index(after) + 1:]

  # R5: exclusions.
  patterns = [main_branch] + configured_exclusions() + args.exclude
  targets = [b for b in branches
             if not any(fnmatch.fnmatchcase(b, p) for p in patterns)]
  print('Syncing: %s' % ' '.join(targets))

  wts = worktree_map()
  skipped = []
  rc = 0
  for branch in targets:
    print('===== %s =====' % branch)
    if contains(branch, main_branch):
      print('up to date')
      continue

    path = wts.get(branch)
    # The map is from the start of the run, and we move the current checkout
    # around, so treat its own branch like an unchecked-out one.
    if path is None or path == here:
      path = here
      reason = dirty_reason(here)
      if reason:
        print('SKIPPED: current checkout (%s) has %s' % (here, reason))
        skipped.append((branch, 'current checkout: ' + reason))
        continue
      if git('branch', '--show-current', cwd=here) != branch:
        git('checkout', branch, cwd=here)
    else:
      reason = dirty_reason(path)
      if reason:
        print('SKIPPED: worktree %s has %s' % (path, reason))
        skipped.append((branch, '%s: %s' % (path, reason)))
        continue

    p = git('merge', main_branch, '--no-edit', cwd=path, check=False)
    print(p.stdout, end='')
    if p.returncode != 0:
      print(p.stderr, end='', file=sys.stderr)
      print('\nCONFLICT merging %s into %s' % (main_branch, branch))
      print('  in: %s' % path)
      print('  %s' % resume_hint(branch))
      sys.exit(1)

  # R7: put the starting checkout back where it was.
  if git('branch', '--show-current', cwd=here) != cur or not cur:
    if dirty_reason(here) is None:
      git('checkout', start, cwd=here)

  if skipped:
    print('\nSkipped (not merged):')
    for branch, why in skipped:
      print('  %s  (%s)' % (branch, why))
    rc = 1
  sys.exit(rc)


if __name__ == '__main__':
  main()
