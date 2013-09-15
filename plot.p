#output as png image
set terminal png

#save file to "domain.png"
set output "domain.png"

#graph title
set title "ab -n 1000 -c 50"

#nicer aspect ratio for image size
set size 1,0.7

# y-axis grid
set grid y

#x-axis label
set xlabel "request"

#y-axis label
set ylabel "response time (ms)"

#plot data from "test.gnuplot" using column 9 with smooth sbezier lines
#and title of "something" for the given data
plot "test.gnuplot" using 9 smooth sbezier with lines title "something"
