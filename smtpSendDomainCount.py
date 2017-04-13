#!/usr/bin/env python

# 2014-03-01, Jannick Sikkema, initalliy created script.
# This script parses EXIM logfiles and generates a count for
# the 30 most popular send domains from the last 24H.

import os
import subprocess
import datetime
import re
from collections import defaultdict


class DomainCounter(object):
    # Define mail directory location, outputfile and binary paths here
    def __init__(self):
        self.base_path = '/opt/mail'
        self.tmp = []
        self.date = datetime.date.today() - datetime.timedelta(days=1)
        self.file_out = '/var/tmp/parsed_exim_files-' + str(self.date.strftime('%Y%m%d')) + '.decompressed'
        self.touch = '/usr/bin/touch'
        self.pbzip = '/usr/bin/pbzip2'

    def parse_log_files(self):
        print 'Generating a total send domain count for:', self.date
        sub_dir = os.listdir(self.base_path)
        for directory in sub_dir:
            if re.search('smtp\d+', directory):
                fileInput = self.base_path + '/' + directory + '/maillog-' + str(self.date.strftime('%Y%m%d')) + '.bz2'
                if not os.path.isfile(self.file_out):
                    subprocess.Popen([self.touch, self.file_out]).communicate()[0]
                with open(self.file_out, 'wb', 0) as output_file:
                    subprocess.check_call([self.pbzip, '-cd', fileInput], stdout=output_file)
                accessFileHandle = open(self.file_out, 'r')
                readFileHandle = accessFileHandle.readlines()
                print "Proccessing %s." % fileInput
                for line in readFileHandle:
                    if '<=' in line and ' for ' in line and '<>' not in line:
                        distinctLine = line.split(' for ')
                        recipientAddresses = distinctLine[1].strip()
                        recipientAddressList = recipientAddresses.strip().split(' ')
                        if len(recipientAddressList) > 1:
                            for emailaddress in recipientAddressList:
                                if '@' in emailaddress:
                                    (login, mailDn) = emailaddress.split("@")
                                    self.tmp.append(mailDn)
                                # Since syslog messages are send through UDP, we need to skip "broken" lines.
                                elif '@' not in emailaddress:
                                    pass
                                    continue
                accessFileHandle.close()
                os.unlink(self.file_out)
        return self.tmp


if __name__ == '__main__':
    domainCounter = DomainCounter()
    result = domainCounter.parse_log_files()
    domainCounts = defaultdict(int)
    top = 30
    for domain in result:
        domainCounts[domain] += 1
    sortedDict = dict(sorted(domainCounts.items(), key=lambda x: x[1], reverse=True)[:int(top)])
    for w in sorted(sortedDict, key=sortedDict.get, reverse=True):
        print '%-3s %s' % (sortedDict[w], w)
