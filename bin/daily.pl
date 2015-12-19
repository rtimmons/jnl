#!/usr/bin/env perl -w
use strict;
use warnings;

use FindBin qw($Bin);
use lib "$Bin/../lib";
use Carp::Heavy;

use jnl qw(dbdir guid open_file today);

sub daily_file_name {
    # confusing: no suffix
    my ($date) = @_;
    return "dxx-$date";
}
sub daily_file_path {
    my ($basedir, $daily_file_name) = @_;
    return "$basedir/$daily_file_name.txt";
}
sub write_file {
    my ($daily_file_name, $jfile) = @_;
    open  JFILE, ">$jfile" or die "Couldn't write $jfile: $!";
    print JFILE ("\n" x 4) . "My Reference: $daily_file_name  \n";
    close JFILE;
}
sub maybe_write_file {
    my ($daily_file_name, $jfile) = @_;
    return if -f $jfile;
    write_file($daily_file_name, $jfile);
}


sub main {
    my $today = today();
    my $daily_file_name = daily_file_name($today);
    my $jfile = daily_file_path(dbdir("daily"), $daily_file_name);
    maybe_write_file($daily_file_name, $jfile);
    open_file($jfile);
}


if ( $0 eq __FILE__ ) {
    main();
}
