#!/usr/bin/env perl -w
use strict;
use warnings;

use FindBin qw($Bin);
use lib "$Bin/../lib";

use Carp::Heavy;

use jnl qw(dbdir open_file today daily_file_name daily_file_path);


sub write_file {
    my ($daily_file_name, $jfile, $conts) = @_;
    open  JFILE, ">$jfile" or die "Couldn't write $jfile: $!";
    print JFILE ("\n" x 4) . "My Reference: $daily_file_name  \n";
    close JFILE;
}
sub maybe_write_file {
    my ($daily_file_name, $jfile, $conts) = @_;
    return if -f $jfile;
    write_file($daily_file_name, $jfile, $conts);
}


sub main {
    my ($date, $conts) = @_;
    my $today = today($date);
    my $daily_file_name = daily_file_name($today);
    my $jfile = daily_file_path(dbdir("daily"), $daily_file_name);
    maybe_write_file($daily_file_name, $jfile, $conts);
    open_file($jfile);
}


if ( $0 eq __FILE__ ) {
    main(@ARGV);
}
