#! /usr/bin/python

import sys
import subprocess
from tempfile import TemporaryFile
from xlwt import Workbook


MSG = \
''' Supply cycles, concurrency increment, requests increment, output file prefix and URL.
    eg. ab_driver.py 10 10 10 test_file http://localhost/

    This will run ab repeatedly, starting at 10 concurrent users and 10 requests.
    It will repeat for the amount given in 'cycles'.  Each cycle will repeat the
    bench 10 times, increasing the requests by 100 each time.

    The above example will lead to, 10 cycles, each will fetch the URL
    http://localhost/ and write the following files:
    test_concurrency_10_requests_10.csv
    test_concurrency_10_requests_10.gnuplot
    test_concurrency_10_requests_10.txt
    test_concurrency_10_requests_10.error (only if an error occurred)
'''


def _process(concurrency, requests, output_file_name, url, workbook=None):
    gnuplot_file = '%s_concurrency_%s_requests_%s.gnuplot' % (output_file_name,
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
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
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
    cfile = open(file_name, 'rb')
    content = cfile.read()
    cfile.close()
    return content


def _write_xl(out, txt, csv, sheet):
    for row_idx, line in enumerate(csv.split('\n')):
        for col_idx, data in enumerate(line.split(',')):
            sheet.write(row_idx, col_idx, data)
    
    col_idx = 4
    for row_idx, line in enumerate(out.split('\n')):
        sheet.write(row_idx, col_idx, line)

    sheet.flush_row_data()    
    return sheet


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

    cycles, r_increment, c_increment, file_prefix, url = sys.argv[1:6]
    cycles = int(cycles)
    r_increment = int(r_increment)
    c_increment = int(c_increment)
    
    workbook = None
    if len(sys.argv) > 6:
        spreadsheet_name = sys.argv[6]
        workbook = Workbook()

    for cycle in range(1, cycles+1):
        concurrency = cycle * c_increment
        for requests in range(0, 1100, 100):
            if requests == 0:
                continue

            out, err, txt, csv = _process(concurrency,
                                          requests,
                                          file_prefix,
                                          url,
                                          workbook) 
            if workbook and not err:
                sheet = workbook.add_sheet('users%s - requests%s' % (cycle, requests))
                _write_xl(out, txt, csv, sheet)
            _print_results(out, err)

    if workbook:
        workbook.save(spreadsheet_name)
        workbook.save(TemporaryFile())
