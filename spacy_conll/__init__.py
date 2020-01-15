from spacy.tokens import Doc, Span

# NOTE: DEPRECATED: import here for backward-compatibility
from spacy_conll.SpacyConllParser import Spacy2ConllParser


class ConllFormatter:
    name = 'conll_formatter'

    def __init__(self, nlp, include_headers=False):
        self.include_headers = include_headers
        # To get the morphological info, we need a tag map
        self.tagmap = nlp.Defaults.tag_map
        self._set_extensions()

    def __call__(self, doc):
        # We need to hook the extensions again when using
        # multiprocessing in Windows
        # see: https://github.com/explosion/spaCy/issues/4903
        self._set_extensions()

        sent_conlls = []
        for sent_idx, sent in enumerate(doc.sents, 1):
            sent_conll = self._get_sent_conll(sent, sent_idx)
            sent_conlls.append(sent_conll)
            sent._.set('conll_format', sent_conll)

        doc._.set('conll_format', '\n'.join(sent_conlls))

        return doc

    def _get_sent_conll(self, span, span_idx=1):
        parsed_sent = ''
        if self.include_headers:
            parsed_sent += f"# sent_id = {span_idx}\n"
            parsed_sent += f"# text = {span.text}\n"

        for word_idx, word in enumerate(span, 1):
            if word.dep_.lower().strip() == 'root':
                head_idx = 0
            else:
                head_idx = word.head.i + 1 - span[0].i

            line_tuple = (
                word_idx,
                word.text,
                word.lemma_,
                word.pos_,
                word.tag_,
                self._get_morphology(word.tag_),
                head_idx,
                word.dep_,
                '_',
                '_'
            )
            parsed_sent += '\t'.join(map(str, line_tuple)) + '\n'

        return parsed_sent

    def _get_morphology(self, tag):
        if not self.tagmap or tag not in self.tagmap:
            return '_'
        else:
            feats = [f"{prop}={val}" for prop, val in self.tagmap[tag].items() if not self._is_number(prop)]
            if feats:
                return '|'.join(feats)
            else:
                return '_'

    def _set_extensions(self):
        if not Span.has_extension('conll_format'):
            Span.set_extension('conll_format', getter=self._get_sent_conll)
        if not Doc.has_extension('conll_format'):
            Doc.set_extension('conll_format', default=None)

    @staticmethod
    def _is_number(s):
        try:
            float(s)
            return True
        except ValueError:
            return False
