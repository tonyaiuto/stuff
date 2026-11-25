# SYNCALL requirements

Draft, to be refined. This records the intended behavior of `SYNCALL`, not the
quirks of the current bash implementation. The tool is being rewritten in
Python (R9). Known deviations of the bash version are listed at the end.

## Purpose

Keep every local working branch current with the repository's main line by
merging the main line into each of them, in one command. Works in plain
checkouts, and in workspaces that mix local branches with git worktrees.

## Requirements

### R1. Refresh the main line from remotes
- When run from the main branch (`main` or `master`), fetch all remotes.
- If the repo has more than one remote (a fork with an upstream), also pull so
  the local main picks up upstream's main.
- When run from any other branch, do not touch the network.

### R2. Determine the integration branch ("MAIN")
- Pick the repo's main line automatically; the user never names it.
- Candidates: `main`, `work`, `master`, `trunk`. Default is `main`.
- If more than one exists, preference is `main` > `master` > `work` > `trunk`.

### R3. Merge MAIN into each selected branch
- For each selected branch, merge MAIN with `--no-edit` (no editor prompt,
  default merge message).
- Print a header per branch so progress is easy to follow.
- Merge, never rebase: branch history is preserved.
- Where the merge happens depends on the branch (see R8):
  - checked out in a worktree: merge there (`git -C <path> merge`).
  - not checked out anywhere: check it out in the current checkout, merge.

### R4. Branch selection
- Default: all local branches except the exclusions in R5.
- Order is deterministic: `git branch` order (sorted by name).
- Resume support, for continuing after a conflict stopped a run:
  - `SYNCALL .`: sync only the branches after the current branch.
  - `SYNCALL <branch>`: sync only the branches after `<branch>`; `<branch>` is
    matched literally, not as a regex.
  - In both cases the named/current branch itself is skipped.
  - `.` must refuse to continue if the current branch is not actually done:
    a merge is still in progress (`MERGE_HEAD` exists) or the branch does not
    yet contain MAIN. It tells the user why.

### R5. Configurable exclusions
- Excluded branches are not merged into. Patterns are shell globs.
- Built-in defaults (used when nothing is configured): `master`, `work`,
  `bazel.main`, `z*`, `*backport*`.
- Configurable through git config, multi-valued, so it works per repo and
  globally:
  - `git config --add syncall.exclude 'z*'`
  - `git config --global --add syncall.exclude '*backport*'`
- Open: whether configured values add to the defaults or replace them.
- Open: command-line `--exclude` / `--include` for one-off runs.

### R6. Stop on conflict
- If a merge conflicts, stop immediately, with a non-zero exit status.
- Leave the conflicted branch as is, and tell the user where it is: the
  branch name, and the worktree path if it is in a worktree.
- Print the exact command to resume once the conflict is resolved.
- After resolving and committing, the user runs `SYNCALL .` from that branch's
  checkout (or `SYNCALL <branch>` from anywhere).

### R7. Return to where the run started
- When the run finishes, restore the checkout the user started in to the
  branch it started on. (Replaces "finish on MAIN"; MAIN may be checked out in
  another worktree and cannot be checked out twice.)
- On a conflict stop (R6) the user is intentionally left on the conflicted
  branch, or in its worktree.

### R8. Worktrees
- Build the branch-to-worktree map from `git worktree list --porcelain`.
- Branches checked out in a worktree are normal merge targets (R3), not
  excluded.
- Dirty worktrees (uncommitted changes, or a merge/rebase already in
  progress) are skipped with a clear warning naming the branch and path.
  Skipped branches are listed in a summary at the end, and the exit status is
  non-zero if any were skipped.
- The same skip rule applies to the current checkout when it needs to check
  out a branch.

### R9. Implementation
- Written in Python (3, standard library only), replacing the bash script.
- Use `/usr/bin/git` directly, bypassing personal git wrappers.
- Do not depend on personal git aliases (`co`, `b`).
- Tell the user which MAIN was chosen, which branches will be synced, and
  which are excluded or skipped, and why.

## Future options (not committed to)

- Dirty worktrees, instead of skipping, offer a choice:
  - ask the user to commit first, then merge;
  - stash, merge, unstash (with care: the unstash can itself conflict).
  - Likely as flags, e.g. `--dirty=skip|ask|stash`.
- `SYNCALL --continue` reading a state file in `git rev-parse --git-common-dir`,
  so resuming works from any worktree without `.`.
- `--keep-going`: after a conflict, skip that branch and continue with the
  others.
- `--dry-run`: show what would be merged where, without changing anything.

## Deferred: other baselines and stacked changes

Deliberately out of scope for now; to be refined another day. Notes so the
thinking is not lost:
- Stacked branches need parent-before-child ordering. Git upstream tracking
  to a local branch (`--set-upstream-to=<branch>`) could record the parent.
- Branches off something other than MAIN (e.g. backports onto a release
  branch) would take a different base. Today the `*backport*` exclusion is
  the stand-in.
- Release lines might need their own refresh from the remote (R1 analogue).
- Needs cycle detection and clear errors for missing or excluded parents.

## Known deviations (current bash implementation vs. above)

- R1: the current-branch detection captures every branch name, so R1 only
  fires when `main`/`master` is the only branch.
- R6: the exit trap always exits 0, so callers cannot tell that a merge
  failed.
- R4: `SYNCALL <branch>` treats the name as a regex and is unquoted.
- R2: the `git b | grep` probes print matching lines as noise.
- R5: exclusions are hard-coded in the script.
- R7: always finishes on MAIN.
- R8: branches checked out in other worktrees are silently excluded.

## Open questions

- R5: do configured exclusions add to the built-in defaults, or replace them?
- R9: should the Python version keep the filename `SYNCALL` (executable with a
  `#!/usr/bin/env python3` shebang), or be `syncall.py` with a thin wrapper?
