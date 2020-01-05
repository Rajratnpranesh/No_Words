'''
gcnn.py

README:

This script defines a graph convolutional network for tensorflow. 

'''
#import torch
import numpy as np
import tensorflow as tf
from models import Model
from models.ops.graph_conv import *
from tensorflow.pyhton.ops import io_ops


#init_op = tf.global_variables_initializer()
class GCNN(Model):

    def __init__(self, **kwargs):
        '''
        '''
        super(GCNN, self).__init__()
        self.model_name = 'Graph-CNN'
        self.define_model(**kwargs)

    def define_model(self, input_shape, kernels_per_layer, kernel_limit,
                        conv_layers, conv_dropouts, pooling_layers, fc_layers, fc_dropouts):
        '''
        Params:
            input_shape - list(int); [nb_nodes, nb_coords, nb_features]
            kernels_per_layer - list(int); list of number of graph kernels per convolution layer
            kernel_limit - list of
            conv_layers - list(int); list of number of filters per convolution layer
            and dropouts
            fc_layers - list(tuples); list of tuples defining number of neurons and dropouts

        '''
        # Inputs
        V, C, A, M = VCAInput(input_shape[0], input_shape[2], input_shape[1])
        is_training = tf.placeholder_with_default(True, shape=())
        self.inputs = [is_training, V, C, M]

        # Graph Convolutions
        for i,_ in enumerate(list(zip(kernels_per_layer,conv_layers,conv_dropouts,pooling_layers))):

            # Graph Kernels for Euchlidean Distances
            A_ = GraphKernels(V, A[0], int(_[0]), kernel_limit, mask=M, training=is_training, namespace='graphkernels_'+str(i)+'_')
            A_ = A_+ A[1:] # ADD Cosine Similarity Back

            # Preform Graph Covolution
            V = GraphConv(V, A_, int(_[1]), activation=tf.nn.leaky_relu, training=is_training,  namespace='graphconv_'+str(i)+'_')
            V = tf.layers.dropout(V, float(_[2]), training=is_training)

            # Sequence Graph Pooling
            if int(_[3]) > 1:
                V,C,A = AverageSeqGraphPool(V,C,int(_[3]), namespace='averseqgraphpool_'+str(i)+'_')
                M = tf.layers.max_pooling2d(tf.expand_dims(M,axis=-1), int(_[3]), int(_[3]))
                M = tf.squeeze(M, axis=-1)


        #shape2 = M.get_shape()

        #f= open("shapesM.txt " ,"w+")
        #f.write(str(shape2))
        #f.close()


        # MultiHeadAttention for shift invarience
        V = MultiHeadAttention(V, int(V.shape[1]))

        #shape1 = V.get_shape()

       # f= open("shapesV.txt " ,"w+")
        #f.write(str(shape1))
       # f.close()
        # Fully Connected Layers
        F = tf.contrib.layers.flatten(V)

        save_op = io_ops._save(filename="/home/raj/mntShare/test/src/saves/F.ckpt", tensor_names=["F"])

        sess = tf.Session()
        sess.run(save_op)


        #tf.io.write_file(filename='final', contents= F)


        #torch.save(F,'file.pt')


    
        '''
		#Shape of the vector

                #Saves the parameters
        saver = tf.train.Saver()
        # run the session
        with tf.Session() as sess:
            sess.run(init_op)
            # save the variable in the disk
            saved_path = saver.save(sess, '/home/raj/mntShare/test/src/saves/saved_variable')
            print('model saved in {}'.format(saved_path))


        '''
        #xyz = tf.print(F)

        #f= open("shapes_print.txt " ,"w+")
        #f.write(str(xyz))
        #f.close()


        #shape = F.get_shape()
        #shapes = print(F)

        #f= open("shapesF.txt " ,"w+")
        #f.write(str(shape))
        #f.close()

        for _ in list(zip(fc_layers,fc_dropouts)):
            F = tf.layers.dense(F, int(_[0]))
            F = tf.layers.batch_normalization(F, training=is_training)
            F = tf.nn.leaky_relu(F)
            F = tf.layers.dropout(F, float(_[1]), training=is_training)

        # Outputs
        self.outputs = [F,]
