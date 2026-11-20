# Agent instructions (OpenG7250)

An agent working in a full work tree of this repository is on the **RE side**,
because the tree contains RE material under `re/`. Follow
[CLEANROOM.md](CLEANROOM.md) without exception.

1. Never work on the product side (`product/`) from a full work tree or from a
   session that has read anything under `re/`. Product agents work only in a
   separate clone whose sparse checkout contains `product/` (and `his/`) but not
   `re/`, and follow `product/spec/AGENTS.md`. Git history in such a clone still
   contains `re/`; product agents never inspect it (`git show`, `git log -p` and
   similar on `re/` paths are forbidden).
2. Put generated artifacts under the git-ignored `re/analysis/analysis/generated/`.
   Never commit decrypted images, decompiler output, traces or dumps.
3. Record findings in `re/analysis/docs/`, as conclusions with addresses and
   sources, without code or listings.
4. Local commits on branches only. No push, pull request, upstream issue or mail
   without an explicit go from the repository owner.
5. The repository owner is Joeri Van Dooren (Guru-RF). Contributors commit
   under their own identity.
6. The working language of the repository is English: documents, code,
   comments, commit messages and issues.
7. Components such as `g7250-emu` keep their own `AGENTS.md`; inside a component,
   its rules apply in addition to these.
