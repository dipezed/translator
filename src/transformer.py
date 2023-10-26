import tensorflow as tf
import numpy as np

from encoder_layer import TransformerEncoder
from decoder_layer import TransformerDecoder

class Transformer(tf.keras.Model):

    def __init__(self,
            nb_encoder,
            nb_decoder,
            nb_heads,
            embed_dim,
            feed_forward_dim,
            max_sequence_length,
            vocab_size,
            dropout=0.0
            ):
        super(Transformer, self).__init__()
        self.loss_metric = tf.keras.metrics.Mean(name="loss")
        self.vocab_size = vocab_size
        self.max_sequence_length = max_sequence_length
        self.encoder = TransformerEncoder(
                nb_encoder,
                nb_heads,
                embed_dim,
                feed_forward_dim,
                max_sequence_length,
                vocab_size,
                dropout=0.0
                )
        self.decoder = TransformerDecoder(
                nb_decoder,
                nb_heads,
                embed_dim,
                feed_forward_dim,
                max_sequence_length,
                vocab_size,
                dropout=0.0
                )
        self.epoch = 0
        self.tokenizer = None
        self.linear = tf.keras.layers.Dense(vocab_size, activation="softmax")
    def call(self, inputs, training = False):
        encoder_inputs = inputs[0]
        decoder_inputs = inputs[1]
        encoder = self.encoder(encoder_inputs, training = training)
        decoder = self.decoder([decoder_inputs, encoder], training = training)
        linear = self.linear(decoder)
        return linear
    def load_data(self, data):
        fr, en = data['fr'], data['en']
        print(fr, "\n\n\n")
        for i in next(fr):
            print(i)
        encoder_inputs = self.tokenizer.texts_to_sequences(fr) 
        decoder_inputs = self.tokenizer.texts_to_sequences(en) 
        encoder_inputs = tf.keras.utils.pad_sequences(
                encoder_inputs,
                maxlen = self.max_sequence_length,
                padding='post'
                )
        decoder_inputs = tf.keras.utils.pad_sequences(
                decoder_inputs,
                maxlen = self.max_sequence_length,
                padding='post'
                )
        return encoder_inputs, decoder_input

    def train_step(self, batch):
        encoder_inputs, decoder_input = self.load_data(batch)
        with tf.GradientTape() as tape:
            prediction = self([encoder_inputs, decoder_inputs])
            true_one_hot = tf.one_hot(decoder_inputs, depth = self.vocab_size)
            loss = self.compiled_loss(true_one_hot, prediction)
        trainable_variable = self.trainable_variables
        gradient_tape = tape.gradient(loss, trainable_variable)
        self.optimizer.apply_gradients(zip(gradient_tape, trainable_variable))
        self.loss_metric.update_state(loss)
        return {"loss":self.loss_metric.result()}

    def generate(self, inputs, tokenizer):
        bs = tf.shape(inputs)[0]
        enc = self.encoder(inputs)
        decoder_inputs = tf.ones((bs, 1), dtype=tf.int32) * \
               tokenizer.config[tokenizer.start_token]
        for i in range(self.max_sequence_length - 1):
            decoder_out = self.decoder([decoder_inputs, enc])
            logits = self.linear(decoder_out)
            logits = tf.argmax(logits, axis = -1, output_type = tf.int32)
            last_logit = tf.expand_dims(logits[:, -1], axis = -1)
            decoder_inputs = tf.concat([decoder_inputs,  last_logit], axis = -1)
        return decoder_inputs 
    def predict_str(self, string, tokenizer):
        inputs = tokenizer.call([string], padding = 0)
        inputs = np.array(inputs)[:, 1:]
        print(inputs)
        print("source = ", tokenizer.decode(inputs[0]))
        predicted = self.generate(inputs, tokenizer)
        str_predicted = tokenizer.decode(predicted.numpy()[0])
        return str_predicted

         
