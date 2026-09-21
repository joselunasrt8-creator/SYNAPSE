# Frozen ordinary control review

Frozen before running SYNAPSE on 2026-09-21 (UTC).

At T0, the README presents phpenv as both a PHP version manager and a PHP
source builder.  `libexec/phpenv` resolves every command by looking up a
`phpenv-<command>` executable.  Before lookup it adds each plugin `bin`
directory to `PATH` and each plugin hook directory to `PHPENV_HOOK_PATH`.
Therefore the dispatcher is already generic: a plugin can supply an `install`
command without a special dispatcher branch.

The bundled `libexec/phpenv-install` is a large, cohesive build workflow.  It
owns source checkout, patching, configuration, compilation, ini generation,
Pyrus, and extension building, and consumes the repository's `etc`, `patches`,
`php-ext`, and install-hook content.  Those files appear coupled to bundled
building.  The separate version-selection/execution commands reference
installed-version directories and shims but do not directly reference the
installer.

The ordinary review therefore already supports the candidate claim: bundled
installation depends on the bundled build subsystem, while selection and
execution of an existing installation do not; the generic plugin path is an
obvious seam for delegation.  It also finds residual coupling that a split
would have to address: README/help install documentation and
`bin/phpenv-install-all-darwin` invoke or advertise `phpenv install`.

No test files were present in the T0 tree, and no build was run because doing
so would clone PHP and mutate external/local build state.  Shell text search
cannot prove all runtime behavior, plugin compatibility, or successful PHP
builds.  The simpler method is direct command-dispatch inspection plus `rg`
reference search; it produced every structural point above.
