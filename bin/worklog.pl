#!/usr/bin/env perl -w
use strict;
use warnings;

use FindBin qw($Bin);
use lib "$Bin/../lib";
use Carp::Heavy;

use jnl qw(dbdir guid open_file);

sub journal_file_name {
    my ($basedir, $guid) = @_;
    return "$basedir/$guid.txt";
}

sub write_file {
    my ($guid, $jfile) = @_;
    open  JFILE, ">$jfile" or die "Couldn't write $jfile: $!";
    print JFILE ("\n" x 4) . "My Reference: $guid  \n";
    close JFILE;
}

sub main {
    my $guid = guid 20;
    my $jfile = journal_file_name(dbdir("worklogs"), $guid);
    write_file($guid, $jfile);
    open_file($jfile);
}


if ( $0 eq __FILE__ ) {
    main();
}
