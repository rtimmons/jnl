# JNL: Directories of Text Files for Daily Work

`jnl` is a set of small scripts to help manage daily worklogs and unsorted scratch files all stored as plaintext.

Actual code is implemented in ugly untested Perl because the code is stupid simple. Important thing is the idea here 💃

## Overview and Installation

    cd ..wherever-you-keep-your-projects..
    
    # Create your Journal Database. Choose whatever or location you'd like. Dropbox works okay.
    mkdir Journal
    # Setup environment variables
    # bash:
    echo "export JNL_DB=$PWD/Journal" >> ~/.bashrc
    # zsh:
    echo "export JNL_DB=$PWD/Journal" >> ~/.zshrc
    # optional: initialize it as a git repo
    git init Journal
    
    # Get the stupid jnl scripts
    git clone https://.../jnl.git
    
    # Add jnl to $PATH
    # bash:
    echo "export PATH=$PWD/jnl/bin:\$PATH" >> ~/.bashrc
    # zsh
    echo "export PATH=$PWD/jnl/bin:\$PATH" >> ~/.zshrc

Then run te various `bin` scripts like a boss.

You may want to create shell aliases. Check out suggestions in `aliases.zshrc`.

There is a "Today's Worklog.app" Apple application. Copy or drag to your Applications directory and rename to end with `.app` to enable.  Funny extension so Spotlight/Alfred & crew don't see this on its own. This little app runs `jdaily` to open today's worklog entry in TextMate (creating if not exists. You can modify it with *Script Editor.app* by dragging it in.

(I cannot recall where I got the cute 'moleskine' icon for the .app. It's entirely possible I stole it and it's copyrighted and you could get into lots of trouble for seeing it. Possibly it's [one of these](http://pica-ae.deviantart.com/art/Moleskine-Icons-91551480)?)

To change the application for opening files, modify `jnl.pm` - see `open -a TextMate.app` for instance.

<!--
TODO: `jnl` wrapper script.
TODO: OS X launcher apps "New Worklog Entry.app", "Today's Entry.app"
TODO: generated index page for daily entries and maybe first line or two of worklog entries
TODO: fancier file-viewer?

TODO: 'quick' symlinks:
- Add @quick(some-identifier). Script to scan for them and create symlinks in 'quick' directory. So if worklogs/QPJX0BGKHPFHZPNJND1K.txt contains @quick(my-novel), symlink `quick/my-novel.txt -> worklogs/QPJX0BGKHPFHZPNJND1K.txt`. Makes it easy to "promote" worklogs items if they become frequently-updated. Potential for "abuse"? Maybe too much structure? Not sure.
- could add suggested git-push hook to re-set them up?
- this is a "cache": how to handle changes & conflicts & things created outside the script?
- if this pans out, maybe dailies are just @daily(2016-01-08)? Harder to enforce uniqueness? Then you have two names - Q4UFG5G2FXTRDJFDZ1N5.txt and 2016-01-08.txt? Not sure if that's really a problem.

Try it out:

    jnl daily
    jnl worklog
    jnl database
    jnl open worklogs
    jnl open daily
    jnl commit

(The `jnl` script doesn't exist yet - you have to go thru the `.pl` scripts manually like an animal. I'm just using shell aliases...)
-->

## Daily & Worklog Files

These files are organized into a "database" which is just a folder. When you run the `jnl` scripts, they look for the `JNL_DB` environment variable for the path to that folder. If not set, the `testdb` directory within this repo will be used so you can play with `jnl`s features or debug while making changes.

There are two kinds of files `jnl` knows about: 

1.  "daily" files

    -   You can create at most one per day
    -   Daily files live in `$JNL_DB/daily`
    -   Use `daily.pl` to open the current day's file (and create it if it doesn't exist)
    
    I use daily files for jotting down things I did, links to pull-requests I created, for putting meeting notes, etc.

    The filenames for daily files are simply e.g. `dxx-2015-12-19.txt`. The `dxx` prefix is to help searching & grepping.

2.  "worklog" files

    -   Create them ad-hoc. They're cheap and lightweight to create and manage.
    -   Worklog files live in `$JNL_DB/worklogs`
    -   Use `worklog.pl` to create a new worklog file and open in TextMate
    -   New files have a random "guid"-esque filename. They are not intended to be sorted by name, but you may want to sort them by date when you open the directory up in Finder to find files

    Create them ad-hoc for composing text, saving snippets of code, drafting ideas, or as buffer space. 

    I like to give myself free-reign to save anything at all into worklog files; I don't treat each one as being important.  Once in the habit of saving random text to worklogs it's very easy to throw one-off shell commands or script output or whatever and search for them later.

    The important files - ones that I often refer back to -  I include the text `@@important`. I have a Finder smart-folder setup that gives me all my important files.

    **NEW**:  
    If you have the line `@quick(some-text)`, the `jquick` command will create
    symlinks in the `$JNL_DB/quick` directory to those files.

    E.g. If the file `MC289YWD6EWRWPYCMTJD.txt` has the contents
    `quick(2016-resolutions)`, then running `jquick` will result in a symlink
    `quick/2016-resolutions.txt` pointing to `MC289YWD6EWRWPYCMTJD.txt`. The
    `some-text` bits between the parentheses must be `a-z`, `A-Z`, `0-9`, `-`,
    or `_`. Other matches will be ignored.

## DayOne Conversion

I used to use DayOne.app for my daily files but it's a pain. But you can export your DayOne journal to plaintext and then use `day1-convert.pl` to convert the entires to daily entries.

## Git and Backup

Don't keep your db folder in here, create a new git repo for it. I like to use `~/Journal`. See above.

If you setup a git repo for your db, the `jnl commit` command will "autopush" your journal with a generated commit message. I don't find there's value in commit messages for these files. If you do, you can always commit like usual.

I like to create a "backup" remote on an external drive and set it up to mirror my local journal repo. So I can just do `git push backup`.
