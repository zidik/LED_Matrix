__author__ = 'Mark'
import yappi

import main


yappi.start()
main.main()
yappi.get_func_stats().print_all()
yappi.get_thread_stats().print_all()
