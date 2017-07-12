eval '(exit $?0)' && eval 'exec perl -S $0 ${1+"$@"}'
    & eval 'exec perl -S $0 $argv:q'
    if 0;

# $Id: rundbtests.pl,v 1.15.2.1.2.1.10.1 2017/05/10 01:43:37 lfiguerres Exp $

use strict;
use Getopt::Std;
use File::Basename;

sub path {
    if ($^O =~ /Win/) {
	return join "\\", @_;
    }
    return join "/", @_;
}

use vars qw/$opt_1 $opt_2 $opt_3 $opt_4 $opt_R $opt_r/;

my $USAGE = "Run the DB Driver quick tests
Syntax: rundbtests [-123r] dataarea
        rundbtests -R productline
        1 - Run just the testview tests.
        2 - Run just the dbcreate/verify tests
        3 - Run just the c qa tests.
        4 - Run just the java regression tests.
        R - Rebuild the qa tests.
        r - Report mode
";

my $rc=getopts('1234Rr');

($rc && @ARGV == 1) or die $USAGE;

my ($da) = @ARGV;

my $GENDIR = $ENV{GENDIR};

if (defined $opt_R) {
    my $LAWDIR = $ENV{LAWDIR};
    chdir path($GENDIR, 'src', 'qa');
    mysystem("cvs -q update -dP");
    if ($ENV{PATH} =~ /;/) {
	# on NT
	mysystem("make.bat clean default");
    } else {
    if (($ENV{OSTYPE} =~ /os400/i)) {
	mysystem("gmake -f makefile.400 clean default");
    } else {
	mysystem("make -f makefile.mk clean default");
    }
    }
    my $lawdirda = path($LAWDIR, $da);
    if (! -d "$LAWDIR/$da") {
	mysystem("mkdir $lawdirda");
	mysystem("configdadb -t $ENV{ENVDBTYPE} $da");
    }
    mysystem("sysload ".path($GENDIR, 'qa', 'bin', 'dbtest80.sysdump')." $da");
    exit(1);
}

unless (defined $opt_1 || defined $opt_2 || defined $opt_3 || defined $opt_4) {
    $opt_1 = 1;
    $opt_2 = 1;
    $opt_3 = 1;
    $opt_4 = 1;
}

use vars qw/%driver %version/;

setver('IBM', 'ibm', "");
if (uc($ENV{ENVDBTYPE}) eq "ORA8") {
    setver('Oracle', 'ora', 8);
} else {
if (uc($ENV{ENVDBTYPE}) eq "ORA9") {
    setver('Oracle', 'ora', 9);
}
else {
    setver('Oracle', 'ora', 10);
}
}
setver('Microsoft', 'msf', 2000);
setver('Postgres', 'pgr', "");

my $Type = "unknown";
my $cmd  = "dmpdict $da vwtst";
$cmd =  "qsh_out -c \"$cmd\"" if ($ENV{OSTYPE} =~ /os400/i);
open PIPE, "$cmd |";
while (<PIPE>) {
    if (/DBType/ && /= (\w+)/) {
	$Type = $1;
    }
}
close PIPE;

$Type eq "unknown" and die "$da is not a valid dbtest80 data area\n";

my $dbid = "$driver{$Type}$version{$Type}";

my $testview = path($GENDIR, 'bin', "test$dbid");

chdir path($GENDIR, 'src', 'dbdrivers', 'tests');

if (defined $opt_1) {
    run_tv("$testview $da ddl", "testviewddl");
    run_tv("$testview $da api", "testview");
    run_tv("$testview $da read | sort", "testviewread");
    run_tv("$testview $da range", "testviewrange");
    run_tv("$testview -r 2 $da all", "testviewall");
}

if (defined $opt_2) {
	scan_buildddl("bld${dbid}ddl -URYq", $da);
	scan_verify("verify${dbid}", $da);
}

if (defined $opt_3) {
    my @tests = glob path($GENDIR, 'qa', 'bin', "dbapi_*");
    foreach my $testpath (@tests) {
	print "\nRun $testpath $da ...\n" if !$opt_r;
	if (mysystem("$testpath $da")) {
	    my $prog = basename($testpath);
	    if ($opt_r) {
		print "$prog FAILED\n";
	    } else {
		print "FAILED FAILED $prog FAILED FAILED FAILED FAILED\n";
	    }
	}
    }
}

if (defined $opt_4) {
	my $LAWDIR = $ENV{LAWDIR};

	my @classpath = (
		path($LAWDIR, 'system'),
		path($GENDIR,'java','jar','lawsonrt.jar'),
		path($GENDIR,'java','jar','lawsec.jar'),
		path($GENDIR,'java','jar','lawsecres.jar'),
		path($GENDIR,'java','ext','jta-spec1_0_1.jar'),
		path($GENDIR,'java','ext','mailapi.jar'),
		path($GENDIR,'java','thirdParty', 'secLS.jar'),
		path($GENDIR,'java','thirdParty', 'jakarta-oro-2.0.jar'),
		path($GENDIR,'java','thirdParty', 'commons-collections.jar'),
		path($GENDIR,'java','thirdParty', 'commons-pool.jar'),
		path($GENDIR,'java','thirdParty', 'commons-codec-1.1.jar'),
		path($GENDIR,'java','thirdParty','js.jar'),
		$ENV{CLASSPATH});
	my @java_ext_dirs = (path($GENDIR, 'java', 'ext'),
              path($GENDIR, 'java', 'impl'));
	my $sep = $^O =~ /Win/ ? ";" : ":";

    my @tests = glob path($GENDIR, 'java', 'classes', 'test', 'lawson',
			  'rdtech', 'db', 'api', "*RegTest.class");
    foreach my $testpath (@tests) {
	my $prog = $1 if $testpath =~ /classes.(.+)\.class/;
	$prog =~ tr [\\\/] [\.\.];

#	my $jcmd = "java -cp ".join($sep, @classpath)." -Djava.ext.dirs=".join($sep, @java_ext_dirs);
	my $jcmd = "java -cp ".join($sep, @classpath);
	if (mysystem("$jcmd $prog $da")) {
	    print STDERR "$prog: FAILED\n";
	}
	}
}

sub setver {
    my ($name, $d, $v) = @_;
    $driver{$name} = $d;
    $version{$name} = $v;
}

sub run_tv {
    my ($cmd, $file) = @_;
    print "Run $cmd ...\n" if !$opt_r;
    unlink "$file.ckout";
    mysystem("$cmd >$file.ckout");
    my $failed = 1;
    if (-f "$file.ckout") {
	if (open PIPE, "diff $file.out $file.ckout |") {
	    $failed = 0;
	    my $count = 0;
	    my $char = "";
	    while (<PIPE>) {
		if (/^1d0$/ || /< \$Id/) {
		} else {
		    if (substr($_,0,1) eq $char) {
			$count += 1;
		    } else {
			print " ...\n" if $count > 20;
			$count = 0;
			$char = substr($_,0,1);
		    }
		    print $_  unless $count>20;
		    $failed = 1;
		}
	    }
	    print " ...\n" if $count > 20;
	    close PIPE;
	}
    } 
    if (defined $opt_r) {
	if ($failed) {
	    print "$cmd: FAILED\n";
	} else {
	    print "$cmd: PASSED\n";
	}
    } elsif ($failed) {
	print "FAILED FAILED FAILED $file FAILED FAILED FAILED\n\n";
    } else {
	print "PASSED\n\n";
    }
}

sub scan_buildddl {
    my ($cmd, $da) = @_;
    print "Run $cmd ...\n" if !$opt_r;
    my $failed = 1;
    if (open PIPE, "$cmd $da 2>&1 |") {
	$failed = 0;
	while (<PIPE>) {
	    if (! /Creating|Dropping|Processing/) {
		print $_;
		$failed = 1;
	    }
	}
	close PIPE;
    }
    
	if ($failed) {
	    print "$cmd: FAILED\n";
	} else {
	    print "$cmd: PASSED\n";
	}
}

sub scan_verify {
    my ($cmd, $da) = @_;
    print "Run $cmd ...\n" if !$opt_r;
    my $failed = 1;
    if (open PIPE, "$cmd $da 2>&1 |") {
	$failed = 0;
      LOOP:
	while (<PIPE>) {
	    last LOOP if /Total/;
	    if (!/Verifying|Checking/) {
		if ($_ !~ /^\W$/) {
		    print $_;
		    $failed = 1;
		}
	    }
	}
	close PIPE;
    }
    
	if ($failed) {
	    print "$cmd: FAILED\n";
	} else {
	    print "$cmd: PASSED\n";
	}
}
sub mysystem
{
    my ($cmd)=@_;

    $cmd =  "qsh_out -c \"$cmd\"" if ($ENV{OSTYPE} =~ /os400/i);
    return system( $cmd );
}

