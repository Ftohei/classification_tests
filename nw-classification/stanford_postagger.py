import os
import tempfile
from subprocess import PIPE
import warnings

from nltk.internals import find_file, find_jar, config_java, java, _java_options
from nltk.tag.api import TaggerI
from nltk import compat

_stanford_url = 'http://nlp.stanford.edu/software'

class StanfordTagger(TaggerI):
    _SEPARATOR = ''
    _JAR = ''


    def __init__(self, model_filename, path_to_jar=None, encoding='utf8', verbose=False, java_options='-mx1000m'):

        if not self._JAR:
            warnings.warn('The StanfordTagger class is not meant to be '
                    'instantiated directly. Did you mean StanfordPOSTagger or StanfordNERTagger?')
        self._stanford_jar = find_jar(
                self._JAR, path_to_jar,
                searchpath=(), url=_stanford_url,
                verbose=verbose)

        self._stanford_model = find_file(model_filename,
                env_vars=('STANFORD_MODELS',), verbose=verbose)
        self._encoding = encoding
        self.java_options = java_options

    @property
    def _cmd(self):
        raise NotImplementedError

    def tag(self, tokens):
        # This function should return list of tuple rather than list of list
        return sum(self.tag_sents([tokens]), [])

    def tag_sents(self, sentences):
        encoding = self._encoding
        default_options = ' '.join(_java_options)
        config_java(options=self.java_options, verbose=False)

        # Create a temporary input file
        _input_fh, self._input_file_path = tempfile.mkstemp(text=True)

        cmd = list(self._cmd)
        cmd.extend(['-encoding', encoding])

        # Write the actual sentences to the temporary input file
        _input_fh = os.fdopen(_input_fh, 'wb')
        _input = '\n'.join((' '.join(x) for x in sentences))
        if isinstance(_input, compat.text_type) and encoding:
            _input = _input.encode(encoding)
        _input_fh.write(_input)
        _input_fh.close()

        # Run the tagger and get the output
        stanpos_output, _stderr = java(cmd, classpath=self._stanford_jar,
                                                       stdout=PIPE, stderr=PIPE)
        stanpos_output = stanpos_output.decode(encoding)

        # Delete the temporary file
        os.unlink(self._input_file_path)

        # Return java configurations to their default values
        config_java(options=default_options, verbose=False)

        return self.parse_output(stanpos_output, sentences)

    def parse_output(self, text, sentences = None):
        # Output the tagged sentences
        tagged_sentences = []
        for tagged_sentence in text.strip().split("\n"):
            sentence = []
            for tagged_word in tagged_sentence.strip().split():
                word_tags = tagged_word.strip().split(self._SEPARATOR)
                sentence.append((''.join(word_tags[:-1]), word_tags[-1]))
            tagged_sentences.append(sentence)
        return tagged_sentences

class StanfordPOSTagger(StanfordTagger):

    _SEPARATOR = '_'
    _JAR = 'stanford-postagger.jar'

    def __init__(self, *args, **kwargs):
        super(StanfordPOSTagger, self).__init__(*args, **kwargs)


    @property
    def _cmd(self):
        return ['edu.stanford.nlp.tagger.maxent.MaxentTagger',
                '-model', self._stanford_model, '-textFile',
                self._input_file_path, '-tokenize', 'false','-outputFormatOptions', 'keepEmptySentences']

