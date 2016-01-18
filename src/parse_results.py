import re
import numpy as np
import scipy.stats
import subprocess

# position of each element in the array
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
# always in the end
LEN=13


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

set style line 10 lt 1 lw 1 pt 6 lc rgb '#777777' ps 1.0
set style line 11 lt 1 lw 1 pt 6 lc rgb '#777777' ps 1.2

set style line 20 lt 1 lw 1 pt 9 lc rgb '#000000' ps 1.0
set style line 21 lt 1 lw 1 pt 9 lc rgb '#000000' ps 1.2

set style line 30 lt 1 lw 1 pt 20 lc rgb '#AAAAAA' ps 1.0
set style line 31 lt 1 lw 1 pt 20 lc rgb '#AAAAAA' ps 1.2

set grid ytics lt 0 lw 1 lc rgb "#bbbbbb"
set grid xtics lt 0 lw 1 lc rgb "#bbbbbb"

set boxwidth 0.9
set style fill solid 1.0 border 0
set style histogram errorbars lw 1 gap 0
set style data histogram


set xlabel '{label_x}'
set ylabel '{label_y}'

set xtics ("Scenario 1" 1.5,  "Scenario 2" 2.5, "Scenario 3" 3.5, "Scenario 4" 4.5, "Scenario 5" 5.5, "Scenario 6" 6.5, "Scenario 7" 7.5, "Scenario 8" 8.5, "Scenario 9" 9.5) rotate by -45 font "LiberationSansNarrow-regular,10"

{range_y}
{range_x}

set xrange [1:10.5]

{extra_opts}

set key inside {key_pos} font "LiberationSansNarrow-regular,10" samplen 2  spacing .75

{plot_line}
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

            # it == 0 means new set of results
            if cur_key not in the_sum:
                the_sum[cur_key] = [[] for i in range(LEN)]

            for it in range(LEN):
                the_sum[cur_key][it].append(arr[it])


    with open("parsed_" + filename, "w+") as fd:
        fd.write("ue rrh conn conn_var dis dis_var bbu_ch bbu_ch_var")
        fd.write(" bw_update bw_update_var bw_max bw_max_var good_cap bood_cap_var")
        fd.write(" bad_cap bad_cap_var avg_rbs_used avg_rbs_used_var avg_throughput avg_throughput_var")
        fd.write(" bad_connection bad_connection_var\n")

        count = 0
        for ue in (100, 500, 1000, ):
            for rrh in (5, 15, 30, ):
                fd.write(str(count) + " " + str(ue) + " " + str(rrh))
                #fd.write(str(ue) + " " + str(rrh))
                for it in range(3, LEN):
                         avg, var = mean_confidence_interval(the_sum[ue, rrh][it])
                         fd.write(" " + str(avg) + " " + str(var))
                fd.write("\n")
                count += 1

if __name__ == '__main__':
    summarize("sdwn_results.txt")
    summarize("nosdwn_results.txt")


    ###########################################################################
    configs = {
        "sdwn": {
            "title": "SDWN",
            "outfile": "sdwn_histo.pdf",
            "configs": { 'label_x': "",
                'label_x': "",
                'label_y': "",
                'range_y': "",
                'range_x': "",
                'key_pos': "top right Right",
                'extra_opts': "",
                },
          },
        "nosdwn": {
            "title": "W/out SDWN",
            "outfile": "nosdwn_histo.pdf",
            "configs": {
                'label_x': "hannels Interfering",
                'label_x': "",
                'label_y': "",
                'range_y': "",
                'range_x': "",
                'key_pos': "top right Right",
                'extra_opts': "",
                },
        },
    }

    ls = 10
    plot_line = 'plot '
    for col in [4, 6, 8, 12]:
        plot_line += '"parsed_sdwn_results.txt" using ' + str(col) + ":" + str(col+1)
        plot_line += ' ls ' + str(ls) + ' title "' + configs['sdwn']['title'] + '"'
        if col < 10:
            plot_line += ', '
        ls += 10

    plot_charts(configs['sdwn']['outfile'], plot_line, configs['sdwn']["configs"], GNUPLOT_SCRIPT_HISTOGRAM)
