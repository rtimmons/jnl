#!/usr/bin/env perl

use strict;
use warnings;

use Carp::Heavy;

use FindBin qw($Bin);
use lib "$Bin/../lib";

use jnl qw(dbdir today daily_file_name daily_file_path dbdir);


my @lines;
my $date;
my $weather;
my $location;
my $header = 0;


my $pending = 0;
sub write_entry {
    if (defined($date)) {
        $date =~ s/\sat\s/ /;
        my $today = today($date);
        my $daily_file_name = daily_file_name($today);
        my $path = daily_file_path(dbdir("daily"), $daily_file_name);
        print "Writing $path\n";
        open  JFILE, ">$path" or croak("Couldn't open $path: $!");
        print JFILE "$_\n" for @lines;
        print JFILE ("\n" x 4) . "My Reference: $daily_file_name  \n";
        close JFILE;
    }
    @lines    = ();
    $date     = undef;
    $weather  = undef;
    $location = undef;
}

# icky, stateful, line-by-line parsing. Consume until 
# we see next 'Date' line then flush.
while(<>) {
    chomp;
    if(!$header && m/^	Date:	(.*?M)$/) {
        write_entry();
        $header = 1;
        $date = $1;
        next;
    }
    if ( $header && m/^	Location:	(.*)/ ) {
        $location = $1;
        next;
    }
    if ( $header && m/^	Weather:	(.*)/ ) {
        $weather = $1;
        next;
    }
    if ( $header ) { $header = 0; }
    push @lines, $_;
}

# clear last entry
write_entry();