#!/usr/bin/env perl -w
use strict;
use warnings;

use FindBin qw($Bin);
use lib "$Bin/../lib";

use Carp::Heavy;

use jnl qw(open_dir);

sub main {
    my ($type) = @_;
        if      ( !defined($type) )            { $type = "worklogs"; }
        if      ( $type =~ qr/^w[orklgs]*$/i ) { $type = "worklogs"; }
        elsif   ( $type =~ qr/^d[ailys]*$/i  ) { $type = "daily";    }
        else    { croak("Unknown open type $type"); }
    
    # now do the thing
    open_dir($type);
}


if ( $0 eq __FILE__ ) {
    main(@ARGV);
}