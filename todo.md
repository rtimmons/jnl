-   2021-05-16: naming and other conventions from Dendron?
        https://www.dendron.so/

-   Summary files:  
    Create `summary/weekly.txt`, `summary/monthly.txt`, etc.
    (Bonus points if can bi-directionally edit them!)

-   "Categories" - use `@category(foo)` and have the file
    symlinked into `foo/${@quick}`.

-   Differentiate between `@quick`, `@daily`, and `@project`.

-   Document the `.project` file (and `@project` tag) functionality.

-   Support actually renaming files based on `@quick`.  
    Seems Alfred and spotlight really don't like to index the names
    of symlinks.

-   Allow an empty `@quick` tag and use the first h1 as the content
    (`# Foo` => `@quick(Foo)`)

-   Settings

    -   if `JNL_DIR` not specified, read settings file `~/.jnl`?
    -   Ignored files (don't require `@noscan` for every file?)
    -   Change tag `@` marker in settings
    -   Change `quick` prefix or output dir in settings

-   interact with filesystem more

    -   support `@name(foo)` tag to rename the actual file. Interact
        with git to do `git mv`?

    -   integrate with text files outside of jnl dir. e.g. recognize
        files with a single line like

            @link(~/todo.txt)

        and treat the `~/todo.txt` as being part of the jnl dir. Would
        be nice for supporting @quick() files that live in github repos,
        etc.

    -   support filtering `@offline` or something tags that get `grep`ed
        into a text file on dropbox or similar for one-way views onto
        mobile

-   hierarchical daily files so current month (week? last N entries?) in
    `daily` but others are in dir by month and/or year.

-   Ignore files with @ignore

-   Alfred workflow (see https://www.alfredapp.com/help/workflows/)

    -   Append to daily
    -   Append to quick
    -   Create as new wl
    -   Open daily
    -   Open quick

-   An actual UI?

    -   Simple UI view app like nv but better
    -   Console app?
    -   Borrow things from [Pext](https://github.com/Pext/Pext)?
    -   generated index page for daily entries and maybe first line or
        two entries
    -   blame view
    -   grep view
    -   group by topic/tag {all sections with particular @tag together}
    -   https://github.com/vinta/awesome-python#command-line-interface-development
    -   What would something like [this](https://github.com/xwmx/nb) do?

-   Support multiple JNL dirs

    -   create bin-stub to call into module / shim copy/paste thing for
        root of db dir (so can use `dirname $0` for `JNL_DIR`)

-   move to proper python module.
    [ftfy](https://github.com/LuminosoInsight/python-ftfy) looks like it
    does this simply and well?

-   smarter `jnl` wrapper script

    -   `jnl daily`
    -   `jnl worklog`
    -   `jnl database`
    -   `jnl open worklogs`
    -   `jnl open daily`
    -   `jnl commit`
    -   `jnl open <guid prefix>`

-   better setup / first-run experience

    -   explain how to modify the `.app` to call `jdaily`
    -   suggested git hook to run `jnl scan`

-   better `jnl search` experience: allow searching for/within
    files modified in last N days.

<!--
Integrate with fancy CI tooling:

[travis-img]: https://travis-ci.org/rtimmons/jnl.svg?branch=master
[travis-url]: https://travis-ci.org/rtimmons/jnl
[coverall-img]: https://coveralls.io/repos/github/rtimmons/jnl/badge.svg?branch=master
[coverall-url]: https://coveralls.io/github/rtimmons/jnl?branch=master
[codacy-image]: https://api.codacy.com/project/badge/Grade/ce0ad20ca59947af86b0f17a5779c804
[codacy-url]: https://www.codacy.com/app/rtimmons/jnl?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=rtimmons/jnl&amp;utm_campaign=Badge_Grade
-->

