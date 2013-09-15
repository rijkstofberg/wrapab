#! /usr/bin/python

import sys
import subprocess
from tempfile import TemporaryFile
from xlwt import Workbook


MSG = \
''' ab_driver.py cycles, concurrency increment, max requests, output file prefix and URL, spreadsheet name
    eg. ab_driver.py 10 10 1000 test_file http://localhost/ test.xls

    This will run ab repeatedly, starting at 10 concurrent users.  Each cycle
    will do a maximum of 1000 requests.  Subsequent cycles will each have 10
    times more users than their direct predecessor.

    The above example will lead to, 10 cycles, each will fetch the URL
    http://localhost/ and write the following files:
    test_concurrency_10_requests_10.csv
    test_concurrency_10_requests_10.tsv  (gnuplot format)
    test_concurrency_10_requests_10.txt (raw output of ab; includes basic stats)
    test_concurrency_10_requests_10.error (only if an error occurred)
    test.xls
'''


def _process(concurrency, requests, output_file_name, url, workbook=None):
    gnuplot_file = '%s_concurrency_%s_requests_%s.tsv' % (output_file_name,
                                                          concurrency,
                                                          requests)
    csv_file = '%s_concurrency_%s_requests_%s.csv' % (output_file_name,
                                                      concurrency,
                                                      requests)
    txt_file = '%s_concurrency_%s_requests_%s.txt' % (output_file_name,
                                                      concurrency,
                                                      requests)
    params = ['ab',
              '-e',
              csv_file,
              '-g',
              gnuplot_file,
              '-c',
              str(concurrency),
              '-n',
              str(requests),
              url]

    process = subprocess.Popen(params,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE)
    stdout, stderr = process.communicate()
    result_file = open(txt_file, 'wb')
    result_file.write(stdout)
    result_file.close()
    if stderr:
        error_file = open(output_file_name + '.error', 'wb')
        error_file.write(stderr)
        error_file.close()
    
    txt_content = csv_content = None
    if workbook:
        txt_content = _get_content(txt_file)
        csv_content = _get_content(csv_file)
            
    return stdout, stderr, txt_content, csv_content


def _get_content(file_name):
    try:
        cfile = open(file_name, 'rb')
        content = cfile.read()
        cfile.close()
        return content
    except IOError:
        return 'No data found'


def _write_xl(txt, csv, sheet):
    for row_idx, line in enumerate(csv.split('\n')):
        for col_idx, data in enumerate(line.split(',')):
            sheet.write(row_idx, col_idx, data)
    
    col_idx = 4
    for row_idx, line in enumerate(txt.split('\n')):
        sheet.write(row_idx, col_idx, line)

    sheet.flush_row_data()    
    return sheet


def _generate_graph(txt):
    return


def _print_results(out, err):
    print '=================================== Result ====================================='
    print out
    print '=================================== Errors ====================================='
    print err
    print '==================================== END ======================================='


if __name__ == '__main__':
    if len(sys.argv) < 6:
        print MSG
        sys.exit(1)

    cycles, c_increment, max_requests, file_prefix, url = sys.argv[1:6]
    cycles = int(cycles)
    max_requests = int(max_requests)
    c_increment = int(c_increment)
    r_increment = max_requests/cycles
    requests_per_cycle = range(0, max_requests+r_increment, r_increment)
    
    workbook = None
    if len(sys.argv) > 6:
        spreadsheet_name = sys.argv[6]
        workbook = Workbook()
    
    for cycle in range(1, cycles+1):
        concurrency = cycle * c_increment
        for requests in requests_per_cycle:
            if requests == 0 or requests < concurrency:
                continue

            out, err, txt, csv = _process(concurrency,
                                          requests,
                                          file_prefix,
                                          url,
                                          workbook) 
            if workbook and not err:
                sheet = workbook.add_sheet(
                    'users%s - requests%s' % (concurrency, requests))
                _write_xl(txt, csv, sheet)
            _print_results(out, err)

    if workbook:
        workbook.save(spreadsheet_name)
        workbook.save(TemporaryFile())
