import torch
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using {device}")

import math, collections.abc, random, copy

from layers import *
from functools import reduce

#max_src_len = 2345
max_src_len = 2369 # rich pbp
max_dst_len = 22

def progress(iterable):
    import os, sys
    if os.isatty(sys.stderr.fileno()):
        try:
            import tqdm
            return tqdm.tqdm(iterable)
        except ImportError:
            return iterable
    else:
        return iterable

class Vocab(collections.abc.MutableSet):
    """Set-like data structure that can change words into numbers and back."""
    def __init__(self):
        words = {'<EOS>', '<UNK>'}
        self.num_to_word = list(words)    
        self.word_to_num = {word:num for num, word in enumerate(self.num_to_word)}
    def add(self, word):
        if word in self: return
        num = len(self.num_to_word)
        self.num_to_word.append(word)
        self.word_to_num[word] = num
    def discard(self, word):
        raise NotImplementedError()
    def __contains__(self, word):
        return word in self.word_to_num
    def __len__(self):
        return len(self.num_to_word)
    def __iter__(self):
        return iter(self.num_to_word)

    def numberize(self, word):
        """Convert a word into a number."""
        if word in self.word_to_num:
            return self.word_to_num[word]
        else: 
            return self.word_to_num['<UNK>']

    def denumberize(self, num):
        """Convert a number into a word."""
        return self.num_to_word[num]

def read_parallel(filename):
    """Read data from the file named by 'filename.'

    The file should be in the format:

    我 不 喜 欢 沙 子 \t i do n't like sand

    where \t is a tab character.

    Argument: filename
    Returns: list of pairs of lists of strings. <EOS> is appended to all sentences.
    """
    data = []
    for line in open(filename):
        fline, eline = line.split('\t')
        fwords = fline.split() + ['<EOS>']
        ewords = eline.split() + ['<EOS>']
        data.append((fwords, ewords))
    return data

def read_mono(filename):
    """Read sentences from the file named by 'filename.' 

    Argument: filename
    Returns: list of lists of strings. <EOS> is appended to each sentence.
    """
    data = []
    for line in open(filename):
        words = line.split() + ['<EOS>']
        data.append(words)
    return data
    
class Encoder(torch.nn.Module):
    """Simplified transformer encoder."""
    
    def __init__(self, vocab_size, dims, layers=4):
        super().__init__()

        # Word embedding
        self.emb = Embedding(vocab_size, dims)

        # Position embedding
        #   - Same as word embedding, but without normalization
        #   - Taking hint from epos, fpos in model 2 to use logit matrix straight up and not accept the normalization done in Embedding
        self.fpos = torch.nn.Parameter(torch.empty(max_src_len, dims))
        torch.nn.init.normal_(self.fpos, std=0.01)

        # Self attention layers
        self.self_attention_layers = torch.nn.ModuleList([SelfAttention(dims) for i in range(layers)])
        self.tanh_layers = torch.nn.ModuleList([TanhLayer(dims, dims, True) for i in range(layers)])

    def forward(self, fnums):
        """Encode a Chinese sentence.

        Argument: Chinese sentence (list of n strings)
        Returns: Chinese word encodings (Tensor of size n,d)"""
        # Encode word as word embedding + pos embedding (3.65)
        # Then, pass through (self attention layer, tanh layer) pairs
        return reduce(
            lambda curr, layer: self.tanh_layers[layer]( # (3.67)
                self.self_attention_layers[layer](curr) # (3.66)
            ),
            range(len(self.self_attention_layers)),
            torch.stack([emb + self.fpos[j] for (j, emb) in enumerate(self.emb(fnums))], 0) # Stack as rows
        )

class Decoder(torch.nn.Module):
    """Simplified transformer decoder."""
    
    def __init__(self, dims, vocab_size, layers=4):
        super().__init__()
        
        # Word embedding
        self.emb = Embedding(vocab_size, dims)

        # Position embedding
        #   - Same as word embedding, but without normalization
        #   - Taking hint from epos, fpos in model 2 to use logit matrix straight up and not accept the normalization done in Embedding
        self.epos = torch.nn.Parameter(torch.empty(max_dst_len, dims))
        torch.nn.init.normal_(self.epos, std=0.01)

        # Self attention layers
        self.self_attention_layers = torch.nn.ModuleList([SelfAttention(dims) for i in range(layers)])
        self.tanh_layers = torch.nn.ModuleList([TanhLayer(dims, dims, True) for i in range(layers)])

        # Final output layer
        self.final_tanh = TanhLayer(2*dims, dims) # input: concat(c, g_prime) (3.72)
        self.final_softmax = SoftmaxLayer(dims, vocab_size)

        # Initial "self attention layers output"
        self.g_prime_0 = torch.nn.Parameter(torch.empty(dims))
        torch.nn.init.normal_(self.g_prime_0, std=0.01)

    def start(self, fencs):
        """Return the initial state of the decoder.

        Argument:
        - fencs (Tensor of size n,d): Source encodings

        For our simple transformer, the state consist of:
            - fencs (used in output's cross attention layer)
            - previous English encodings (input adds an encoding each time)
            - last g prime value (input overwrites each time, output uses)
        """
        
        return (fencs, [], self.g_prime_0)

    def input(self, state, enum):
        """Read in an English word (enum) and compute a new state from
        the old state (state).

        Arguments:
            state: Old state of decoder
            enum:  Next English word (int)

        Returns: New state of decoder
        """
        (fencs, pvs_encs, g_prime_pvs) = state
        # English word encoding is word emebedding plus position embedding (3.68)
        # Next English position is the number of already known words, assuming 0-based positions
        pvs_encs += [self.emb(enum) + self.epos[len(pvs_encs)]]

        # Allow multiple self attention layers for kicks
        attention_results = reduce(
            lambda curr, layer: self.tanh_layers[layer]( # (3.70)
                self.self_attention_layers[layer](curr) # (3.69)
            ),
            range(len(self.self_attention_layers)),
            torch.stack(pvs_encs, 0) # Stack previous encodings as rows (u's in 3.69)
        )
        # Only actually need about last row of self attention output (3.71)
        # However, it seems that we need to recompute the entire matrix, starting from the previous encodings as rows matrix, each time to match the book equations (3.69-3.71)
        g_prime = attention_results[-1]

        return (fencs, pvs_encs, g_prime)

    def output(self, state):
        """Compute a probability distribution over the next English word.

        Argument: State of decoder

        Returns: Vector of log-probabilities (tensor of size len(evocab))
        """
        
        (H_prime, pvs_encs, g_prime_pvs) = state

        # Cross attend b/w encoder output (self attention on input)
        # and g prime (self attention on output)
        c = attention(g_prime_pvs, H_prime, H_prime) # (3.71)
        o = self.final_tanh(torch.cat((c, g_prime_pvs))) # (3.72)

        # One last softmax for good measure
        p = self.final_softmax(o) # (3.73)
        return p

class Model(torch.nn.Module):
    """A simplified version of a transformer.

    You are free to modify this class, but you probably don't need to;
    it's probably enough to modify Encoder and Decoder.
    """
    def __init__(self, fvocab, dims, evocab):
        super().__init__()

        # Store the vocabularies inside the Model object
        # so that they get loaded and saved with it.
        self.fvocab = fvocab
        self.evocab = evocab
        
        # Try smaller # of layers as recommended due to small data size
        self.encoder = Encoder(len(fvocab), dims, layers=3)
        self.decoder = Decoder(dims, len(evocab), layers=3)

        # This is just so we know what device to create new tensors on        
        self.dummy = torch.nn.Parameter(torch.empty(0, device=device))

    def logprob(self, fwords, ewords):
        """Return the log-probability of a sentence pair.

        Arguments:
            fwords: source sentence (list of str)
            ewords: target sentence (list of str)

        Return:
            log-probability of ewords given fwords (scalar)"""

        fnums = torch.tensor([self.fvocab.numberize(f) for f in fwords], device=self.dummy.device)
        fencs = self.encoder(fnums)
        state = self.decoder.start(fencs)
        logprob = 0.
        for eword in ewords:
            o = self.decoder.output(state)
            enum = self.evocab.numberize(eword)
            logprob += o[enum]
            state = self.decoder.input(state, enum)
        return logprob

    def translate(self, fwords):
        """Translate a sentence using greedy search.

        Arguments:
            fwords: source sentence (list of str)

        Return:
            ewords: target sentence (list of str)
        """
        
        fnums = torch.tensor([self.fvocab.numberize(f) for f in fwords], device=self.dummy.device)
        fencs = self.encoder(fnums)
        state = self.decoder.start(fencs)
        ewords = []
        for i in range(max_dst_len):
            o = self.decoder.output(state)
            enum = torch.argmax(o).item()
            eword = self.evocab.denumberize(enum)
            if eword == '<EOS>': break
            ewords.append(eword)
            state = self.decoder.input(state, enum)
        return ewords

if __name__ == "__main__":
    import argparse, sys, os
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--train', type=str, help='training data')
    parser.add_argument('--dev', type=str, help='development data')
    parser.add_argument('infile', nargs='?', type=str, help='test data to translate')
    parser.add_argument('-o', '--outfile', type=str, help='write translations to file')
    parser.add_argument('--load', type=str, help='load model from file')
    parser.add_argument('--save', type=str, help='save model in file')
    args = parser.parse_args()

    if args.train:
        # Read training data and create vocabularies
        traindata = read_parallel(args.train)

        fvocab = Vocab()
        evocab = Vocab()
        for fwords, ewords in traindata:
            fvocab |= fwords
            evocab |= ewords

        # Create model
        m = Model(fvocab, 128, evocab) # try increasing 64 to 128 or 256
        m.to(device)
        
        if args.dev is None:
            print('error: --dev is required', file=sys.stderr)
            sys.exit()
        devdata = read_parallel(args.dev)
            
    elif args.load:
        if args.save:
            print('error: --save can only be used with --train', file=sys.stderr)
            sys.exit()
        if args.dev:
            print('error: --dev can only be used with --train', file=sys.stderr)
            sys.exit()
        m = torch.load(args.load, map_location=torch.device('cpu')) # don't put model on gpu for test translations

    else:
        print('error: either --train or --load is required', file=sys.stderr)
        sys.exit()

    if args.infile and not args.outfile:
        print('error: -o is required', file=sys.stderr)
        sys.exit()

    if args.train:
        opt = torch.optim.Adam(m.parameters(), lr=0.0003)

        best_dev_loss = None
        for epoch in range(10):
            random.shuffle(traindata)

            ### Update model on train

            train_loss = 0.
            train_ewords = 0
            for fwords, ewords in progress(traindata):
                loss = -m.logprob(fwords, ewords)
                opt.zero_grad()
                loss.backward()
                opt.step()
                train_loss += loss.item()
                train_ewords += len(ewords) # includes EOS

            ### Validate on dev set and print out a few translations
            
            dev_loss = 0.
            dev_ewords = 0
            for line_num, (fwords, ewords) in enumerate(devdata):
                dev_loss -= m.logprob(fwords, ewords).item()
                dev_ewords += len(ewords) # includes EOS
                if line_num < 10:
                    translation = m.translate(fwords)
                    print(' '.join(translation))

            if args.save:
                torch.save(m, os.path.join(args.save, f'{epoch+1}.model'))
            if best_dev_loss is None or dev_loss < best_dev_loss:
                best_model = copy.deepcopy(m)
                if args.save:
                    best_file = open(os.path.join(args.save, 'best'), 'w')
                    best_file.write(f'{epoch+1}')
                    best_file.close()
                best_dev_loss = dev_loss

            print(f'[{epoch+1}] train_loss={train_loss} train_ppl={math.exp(train_loss/train_ewords)} dev_ppl={math.exp(dev_loss/dev_ewords)}', flush=True)
            
        m = best_model

    ### Translate test set

    if args.infile:
        with open(args.outfile, 'w') as outfile:
            for fwords in read_mono(args.infile):
                translation = m.translate(fwords)
                print(' '.join(translation), file=outfile)
