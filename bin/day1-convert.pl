#!/usr/bin/env perl

use strict;
use warnings;

use Carp::Heavy;

my @lines;
my $date;
my $weather;
my $location;
my $header = 0;


my $pending = 0;
sub write_entry {
    if (defined($date)) {
        print "$date\n";
        print join("\n", @lines);
        print "\n==========================================\n";        
    }
    @lines    = ();
    $date     = undef;
    $weather  = undef;
    $location = undef;
}


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
