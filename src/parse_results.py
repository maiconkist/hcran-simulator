import re
import numpy as np
import scipy.stats
import subprocess

# position of each element in the original file
UE=0
RRH=1
IT=2
CONN=3
DIS=4
BBU_CH=5
BW_UPDATE=6
BW_MAX=7
GOOD_CAP=8
BAD_CAP=9
AVG_RBS_USED=10
AVG_THROUGHPUT=11
BAD_CONN=12
BAD_CONN_SUM=13
BAD_CONN_AVG=14
NO_UES_TIME=15
POWER_CONSUMED=16
IDLE_MSG=17
WAKE_UP_MSG=18
# always in the end
LEN=19

# position of element in the PARSED file:
# position in original file * 2 - 2

def mean_confidence_interval(data, confidence=0.95):
    a = np.array(data) #pylint: disable=E1101
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a) #pylint: disable=E1101

    #ATENTCAO: MUDAR DISTRIBUICAO
    h = se * scipy.stats.t._ppf((1+confidence)/2., n-1) #pylint: disable=E1101
    return m, h


GNUPLOT_SCRIPT_HISTOGRAM= """
set term pdf enhanced dashed size 4,3
set output '{outfile}'

set style line 20 lt 1 lw 1 pt 9 lc rgb '#000000' ps 1.0
set style line 21 lt 1 lw 1 pt 9 lc rgb '#000000' ps 1.2

set style line 10 lt 1 lw 1 pt 6 lc rgb '#666666' ps 1.0
set style line 11 lt 1 lw 1 pt 6 lc rgb '#666666' ps 1.2

set style line 30 lt 1 lw 1 pt 20 lc rgb '#AAAAAA' ps 1.0
set style line 31 lt 1 lw 1 pt 20 lc rgb '#AAAAAA' ps 1.2

set style line 40 lt 1 lw 1 pt 20 lc rgb '#FFFFFF' ps 1.0
set style line 41 lt 1 lw 1 pt 20 lc rgb '#FFFFFF' ps 1.2

set grid ytics lt 0 lw 1 lc rgb "#bbbbbb"
set grid xtics lt 0 lw 1 lc rgb "#bbbbbb"

set style fill solid 1.0 border 0
set style data histogram
set style histogram errorbars lw 1 gap 1
set boxwidth 0.20

set tics scale 0
set xlabel '{label_x}'
set ylabel '{label_y}'

set xtics ("Scenario 1" 1.0,  "Scenario 2" 2, "Scenario 3" 3, "Scenario 4" 4, "Scenario 5" 5, "Scenario 6" 6, "Scenario 7" 7, "Scenario 8" 8, "Scenario 9" 9) rotate by -45 font "LiberationSansNarrow-regular,10"

{range_y}
{range_x}

set xrange [0.375:10]

{extra_opts}

set key inside {key_pos} font "LiberationSansNarrow-regular,10" samplen 2  spacing .75

{plot_line}
"""



R_SCRIPT_PIE= """
data <- read.table("parsed_sdwn_results.txt", header=TRUE)
pct <- round(slices/sum(slices)*100)
title <- paste(title, pct) # add percents to labels
title <- paste(title,"%",sep="") # ad % to labels

pdf("{outfile}")

{plot_line}

dev.off()
"""



def plot_charts(outfile, plot_line, configs, script = GNUPLOT_SCRIPT_HISTOGRAM):
    #Grays
    tmp = script.format(
            plot_line = plot_line,
            outfile = outfile,
            label_y = configs['label_y'],
            range_y = configs['range_y'],
            label_x = configs['label_x'],
            range_x = configs['range_x'],
            key_pos = configs['key_pos'] if 'key_pos' in configs else 'bottom center',
            extra_opts = configs["extra_opts"] if "extra_opts" in configs else ""
        )

    print "----- Plotting ", outfile
    proc = subprocess.Popen(['gnuplot'], shell = True, stdin = subprocess.PIPE)
    proc.communicate( tmp )


def summarize(filename):

    the_sum = {}
    cur_it = None
    cur_key = None

    with open(filename, 'r') as fd:
        next(fd)

        for line in fd:
            arr = line.split(' ')
            # arr to float
            arr = [float(i) for i in arr]

            cur_key = (arr[UE], arr[RRH])

            # cur_key not appeared
            if cur_key not in the_sum:
                the_sum[cur_key] = [[] for i in range(LEN)]

            for it in range(LEN):
                the_sum[cur_key][it].append(arr[it])

            #scaling
            the_sum[cur_key][AVG_RBS_USED][-1] *= 100.0

    with open("parsed_" + filename, "w+") as fd:
        fd.write("scenario ue rrh conn conn_var dis dis_var bbu_ch bbu_ch_var")
        fd.write(" bw_update bw_update_var bw_max bw_max_var good_cap bood_cap_var")
        fd.write(" bad_cap bad_cap_var avg_rbs_used avg_rbs_used_var avg_throughput avg_throughput_var")
        fd.write(" bad_connection bad_connection_var bad_conn_sum bad_conn_sum_var bad_conn_avg_avg bad_conn_avg_var avg_rrh_idle_time rrh_idle_time_var avg_power_consumed power_consumed_var")
        fd.write(" avg_idle_op idle_op_var avg_wake_op wake_op_var\n")

        count = 0
        for ue in (100, 500, 1000, ):
            for rrh in (5, 15, 30, ):
                fd.write(str(count) + " " + str(ue) + " " + str(rrh))
                for col in range(3, LEN):
                         avg, var = mean_confidence_interval(the_sum[ue, rrh][col])
                         if col not in [POWER_CONSUMED, NO_UES_TIME, ]:
                                fd.write(" " + str(avg) + " " + str(var))
                         elif col == POWER_CONSUMED:
                                fd.write(" " + str(avg * 6 / rrh) + " " + str(var/10.0))
                         elif col == NO_UES_TIME:
                                IDLE_PW = 4.3 / 3600.0 # energy consumed per second
                                FULL_PW = 6.8 / 3600.0 # energy consumed per second

                                fd.write(" " + str(avg) + " " + str(var))
                                #fd.write(" " + str((avg * IDLE_PW + ((rrh * 600.0 - avg) * FULL_PW))/rrh) + " " + str(0))
                fd.write("\n")
                count += 1

if __name__ == '__main__':
    summarize("sdwn_results.txt")
    summarize("nosdwn_results.txt")

    # SDWN
    configs = {
        'message_bars':{
            'columns': [4, 6, 8, 10],
            'files': ['parsed_sdwn_results.txt', ],
            'col_title': {
                'parsed_sdwn_results.txt': {
                    4: "Connections",
                    6: "Disconnections",
                    8: "BBU Change",
                    10:"BW Update",
                }
            },
            "outfile": "sdwn_histo.pdf",
            "configs": { 'label_x': "",
                'label_x': "",
                'label_y': "",
                'range_y': "set yrange [0:*]",
                'range_x': "",
                'key_pos': "top left Left",
                'extra_opts': 'set format y "%.0s %c";',
                },
          },
        'comparison_throughput':{
            'columns': [20, ],
            'files': ['parsed_sdwn_results.txt', 'parsed_nosdwn_results.txt'],
            'col_title': {
                'parsed_sdwn_results.txt': {
                    20: 'With SDWN'
                },
                'parsed_nosdwn_results.txt': {
                    20: 'Without SDWN'
                },
            },
            "outfile": "comparison_throughput.pdf",
            "configs": { 'label_x': "",
                'label_x': "",
                'label_y': "Throughput [Mbps]",
                'range_y': "set yrange [0:*]",
                'range_x': "",
                'key_pos': "top right Right",
                'extra_opts': 'set format y "%.0s %c"; set ytics 1000000;',
                },
          },
        'comparison_rb_used_per':{
            'columns': [18, ],
            'files': ['parsed_sdwn_results.txt', 'parsed_nosdwn_results.txt'],
            'col_title': {
                'parsed_sdwn_results.txt': {
                    18: 'With SDWN'
                },
                'parsed_nosdwn_results.txt': {
                    18: 'Without SDWN'
                },
            },
            "outfile": "comparison_rb_used_per.pdf",
            "configs": { 'label_x': "",
                'label_x': "",
                'label_y': "RBs allocated [%]",
                'range_y': "set yrange [0:*]",
                'range_x': "",
                'key_pos': "top left Left",
                'extra_opts': 'set format y "%.0s %c"; set ytics 10;',
                },
          },
        'thoughput_comparison':{
            'columns': [20, ],
            'files': ['parsed_sdwn_results.txt', 'parsed_nosdwn_results.txt'],
            'col_title': {
                'parsed_sdwn_results.txt': {
                    20: 'With SDWN'
                },
                'parsed_nosdwn_results.txt': {
                    20: 'Without SDWN'
                },
            },
            "outfile": "thoughput_comparison.pdf",
            "configs": { 'label_x': "",
                'label_x': "",
                'label_y': "Avg. Throughput [Mbps]",
                'range_y': "set yrange [0:*]",
                'range_x': "",
                'key_pos': "top right Right",
                'extra_opts': 'set format y "%.0s %c"; set ytics 1000000;',
                },
          },
        'bad_connections':{
            'columns': [22, ],
            'files': ['parsed_sdwn_results.txt', 'parsed_nosdwn_results.txt'],
            'col_title': {
                'parsed_sdwn_results.txt': {
                    22: 'With SDWN'
                },
                'parsed_nosdwn_results.txt': {
                    22: 'Without SDWN'
                },
            },
            "outfile": "bad_connections_comparison.pdf",
            "configs": { 'label_x': "",
                'label_x': "",
                'label_y': "Bad connections",
                'range_y': "set yrange [0:5000]",
                'range_x': "",
                'key_pos': "top left Left",
                'extra_opts': 'set format y "%.0s %c"; set ytics 1000;',
                },
          },
        'rrh_idle_time':{
            'columns': [28, ],
            'files': ['parsed_sdwn_results.txt', 'parsed_nosdwn_results.txt'],
            'col_title': {
                'parsed_sdwn_results.txt': {
                    28: 'With SDWN'
                },
                'parsed_nosdwn_results.txt': {
                    28: 'Without SDWN'
                },
            },
            "outfile": "rrh_idle_time.pdf",
            "configs": { 'label_x': "",
                'label_x': "",
                'label_y': "Total RRH Idle Time ",
                'range_y': "",
                'range_x': "",
                'key_pos': "top right Right",
                'extra_opts': '',
                },
          },
        'energy_consumed':{
            'columns': [30, ],
            'files': ['parsed_sdwn_results.txt', 'parsed_nosdwn_results.txt'],
            'col_title': {
                'parsed_sdwn_results.txt': {
                    30: 'With SDWN'
                },
                'parsed_nosdwn_results.txt': {
                    30: 'Without SDWN'
                },
            },
            "outfile": "energy_consumed.pdf",
            "configs": { 'label_x': "",
                'label_x': "",
                'label_y': "Avg. Energy Used per RRH [W] ",
                'range_y': "set yrange[0:10]",
                'range_x': "",
                'key_pos': "top right Right",
                'extra_opts': '',
                },
          },
    }


    for chart in ['message_bars', 'comparison_throughput', 'comparison_rb_used_per', 'bad_connections', 'thoughput_comparison', 'rrh_idle_time', 'energy_consumed']:
        ls = 10
        plot_line = 'plot '

        shift = 0.2 + (0.20 * len(configs[chart]['files']) * len(configs[chart]['columns']))/-2

        #
        #if col == 4:
        #    shift=-0.30
        #elif col == 6:
        #    shift=-0.10
        #elif col == 8:
        #    shift=0.10
        #elif col == 12:
        #    shift=0.30

        for col in configs[chart]['columns']:

            for f in configs[chart]['files']:
                plot_line += '"' + f + '" using ($0+' + str(shift) + '):' + str(col) + ":" + str(col+1)
                plot_line += ' w boxerrorbars ls ' + str(ls) + ' title "' + configs[chart]['col_title'][f][col] + '"'
                plot_line += ', '

                ls += 10
                shift += 0.2

        plot_charts(configs[chart]['outfile'], plot_line, configs[chart]["configs"], GNUPLOT_SCRIPT_HISTOGRAM)


    ### R plot
    data = 'title <- c("Connections", "Disconnections", "BBU Change", "BW Update")\n'
    for scenario in range(1, 10):

        data += 'slices <- c('
        #for col in [3, 5, 7, 9]:
        for col in [4, 6, 8, 10]:
            data += "data[%d,%d]" % (scenario, col)
            if col < 9:
                data += ","
        data += ')\n'

        print "----- Plotting ",
        proc = subprocess.Popen(['R --no-save'], shell = True, stdin = subprocess.PIPE)
        proc.communicate(data + R_SCRIPT_PIE.format(
            plot_line = 'pie(slices, title, main="Scenario ' + str(scenario) + '", col=gray.colors(4))',
            outfile = "pie_scenario_" + str(scenario) + ".pdf"
            )
        )
