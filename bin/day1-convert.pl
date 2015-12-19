#!/usr/bin/env perl

use strict;
use warnings;

use Carp::Heavy;

use FindBin qw($Bin);
use lib "$Bin/../lib";

use jnl qw(dbdir today);


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
        print "$today\n";
        print join("\n", @lines);
        print "\n==========================================\n";        
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
