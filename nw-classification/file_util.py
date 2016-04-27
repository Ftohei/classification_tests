import codecs

def write_to_file(output_file, string):
    with codecs.open(output_file,'a+',encoding='utf-8') as f:
        try:
            f.writelines(string + "\n")
        except UnicodeEncodeError:
            print "Encoding Error: %s" % string

error = '/Users/Fabian/Documents/Arbeit/AG_SD/klassifikator_tests/errors.txt'
output = '/Users/Fabian/Documents/Arbeit/AG_SD/klassifikator_tests/output_cross_val.txt'
pred_dir = '/Users/Fabian/Documents/Arbeit/AG_SD/klassifikator_tests/pred_tests/'
ablation = '/Users/Fabian/Documents/Arbeit/AG_SD/klassifikator_tests/ablation.txt'

ana_dir = '/Users/Fabian/Documents/Arbeit/AG_SD/klassifikator_tests/analysis/'
test = '/Users/Fabian/Desktop/tests.txt'

def write(string,mode='output',filename=''):
    if mode=='error':
        write_to_file(error,string)
    elif mode=='output':
        write_to_file(output,string)
    elif mode=='pred':
        write_to_file(pred_dir+filename,string)
    elif mode=='test':
        write_to_file(test,string)
    elif mode=='analysis':
        write_to_file(ana_dir+filename,string)
    elif mode=='ablation':
        write_to_file(ablation,string)
