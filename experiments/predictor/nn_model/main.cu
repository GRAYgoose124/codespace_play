#include <iostream>
#include <cuda_runtime.h>
#include <cmath>
#include <vector>
#include <cstdlib>
#include <algorithm>
#include <iterator>

#define CUDA_CALL(x)                                                                                                            \
    {                                                                                                                           \
        const cudaError_t a = (x);                                                                                              \
        if (a != cudaSuccess)                                                                                                   \
        {                                                                                                                       \
            std::cerr << "CUDA Runtime Error: " << cudaGetErrorString(a) << " at " << __FILE__ << ":" << __LINE__ << std::endl; \
            exit(EXIT_FAILURE);                                                                                                 \
        }                                                                                                                       \
    }

// Network parameters
const int input_size = 27;
const int hidden_size = 128;
const int output_size = 27;
const float learning_rate = 0.0001;

// Activation function
__device__ float sigmoid(float x)
{
    return 1.0f / (1.0f + exp(-x));
}

__device__ float sigmoid_derivative(float x)
{
    float s = sigmoid(x);
    return s * (1.0f - s);
}

// Forward pass kernel
__global__ void forward_pass(float *x, float *y_pred, float *d_input_hidden_weights, float *d_hidden_output_weights, float *d_hidden_bias, float *d_output_bias, float *hidden_layer_output)
{
    int tid = threadIdx.x;

    // Calculate hidden layer activations
    float h_value = 0.0;
    for (int i = 0; i < input_size; i++)
    {
        h_value += d_input_hidden_weights[tid * input_size + i] * x[i];
    }
    h_value += d_hidden_bias[tid];
    hidden_layer_output[tid] = sigmoid(h_value);

    // Calculate output layer activations (one thread calculates one output neuron's value)
    float o_value = 0.0;
    for (int j = 0; j < hidden_size; j++)
    {
        o_value += d_hidden_output_weights[tid * hidden_size + j] * hidden_layer_output[j];
    }
    o_value += d_output_bias[tid];
    y_pred[tid] = sigmoid(o_value);
}

// Backward pass kernel
__global__ void backward_pass(float *x, float *y, float *y_pred, float *d_input_hidden_weights, float *d_hidden_output_weights, float *d_hidden_bias, float *d_output_bias, float *hidden_layer_output)
{
    int tid = threadIdx.x;

    // Calculate error at the output
    float delta_output = (y[tid] - y_pred[tid]) * sigmoid_derivative(y_pred[tid]);

    // Update output weights and bias
    for (int j = 0; j < hidden_size; j++)
    {
        d_hidden_output_weights[tid * hidden_size + j] += learning_rate * delta_output * hidden_layer_output[j];
    }
    d_output_bias[tid] += learning_rate * delta_output;

    // Calculate error for hidden layer
    float delta_hidden = 0.0;
    for (int k = 0; k < output_size; k++)
    {
        delta_hidden += d_hidden_output_weights[k * hidden_size + tid] * delta_output;
    }

    delta_hidden *= sigmoid_derivative(hidden_layer_output[tid]);

    // Update input weights and bias
    for (int i = 0; i < input_size; i++)
    {
        d_input_hidden_weights[tid * input_size + i] += learning_rate * delta_hidden * x[i];
    }
    d_hidden_bias[tid] += learning_rate * delta_hidden;
}

void train(float *x, float *y, float *d_input_hidden_weights, float *d_hidden_output_weights, float *d_hidden_bias, float *d_output_bias)
{
    float *d_x, *d_y, *y_pred, *hidden_layer_output;

    CUDA_CALL(cudaMalloc(&d_x, input_size * sizeof(float)));
    CUDA_CALL(cudaMalloc(&d_y, output_size * sizeof(float)));
    CUDA_CALL(cudaMalloc(&y_pred, output_size * sizeof(float)));
    CUDA_CALL(cudaMalloc(&hidden_layer_output, hidden_size * sizeof(float)));

    CUDA_CALL(cudaMemcpy(d_x, x, input_size * sizeof(float), cudaMemcpyHostToDevice));
    CUDA_CALL(cudaMemcpy(d_y, y, output_size * sizeof(float), cudaMemcpyHostToDevice));

    for (int epoch = 0; epoch < 1000; epoch++)
    { // Assuming 1000 epochs for demonstration
        forward_pass<<<1, hidden_size>>>(d_x, y_pred, d_input_hidden_weights, d_hidden_output_weights, d_hidden_bias, d_output_bias, hidden_layer_output);
        backward_pass<<<1, hidden_size>>>(d_x, d_y, y_pred, d_input_hidden_weights, d_hidden_output_weights, d_hidden_bias, d_output_bias, hidden_layer_output);
    }

    cudaFree(d_x);
    cudaFree(d_y);
    cudaFree(y_pred);
    cudaFree(hidden_layer_output);
}

void printWeightsAndBiases(float *d_weights, int rows, int cols, const char *name)
{
    std::vector<float> h_weights(rows * cols);

    // Copy from device to host
    CUDA_CALL(cudaMemcpy(h_weights.data(), d_weights, rows * cols * sizeof(float), cudaMemcpyDeviceToHost));

    std::cout << name << ":" << std::endl;
    for (int i = 0; i < rows; ++i)
    {
        for (int j = 0; j < cols; ++j)
        {
            std::cout << h_weights[i * cols + j] << " ";
        }
        std::cout << std::endl;
    }
}

void printBias(float *h_bias, int size, const char *name)
{
    std::cout << name << ":" << std::endl;
    for (int i = 0; i < size; ++i)
    {
        std::cout << h_bias[i] << " ";
    }
    std::cout << std::endl;
}

std::vector<float> charToOneHot(char c)
{
    std::vector<float> oneHot(input_size, 0.0f);
    int index = c - 'a';
    if (index >= 0 && index < input_size)
    {
        oneHot[index] = 1.0f;
    }
    else
    {
        oneHot[input_size - 1] = 1.0f; // Let's use the last position for any non a-z character
    }
    return oneHot;
}

std::vector<std::vector<float>> stringToInputData(const std::string &s)
{
    std::vector<std::vector<float>> data;
    for (char c : s)
    {
        data.push_back(charToOneHot(c));
    }
    return data;
}

void initializeWeightsAndBiases(float **d_weights, int size)
{
    std::vector<float> h_weights(size);
    for (auto &w : h_weights)
    {
        w = (rand() / float(RAND_MAX)) * sqrt(2.0 / size);
    }
    CUDA_CALL(cudaMalloc((void **)d_weights, size * sizeof(float)));
    cudaMemcpy(*d_weights, h_weights.data(), size * sizeof(float), cudaMemcpyHostToDevice);
}

std::string predict(const std::string &input_str, float *d_input_hidden_weights, float *d_hidden_output_weights, float *d_hidden_bias, float *d_output_bias)
{
    auto inputData = stringToInputData(input_str);
    float *d_x, *y_pred, *hidden_layer_output;
    std::vector<float> h_output(output_size);

    CUDA_CALL(cudaMalloc(&d_x, input_size * sizeof(float)));
    CUDA_CALL(cudaMalloc(&y_pred, output_size * sizeof(float)));
    CUDA_CALL(cudaMalloc(&hidden_layer_output, hidden_size * sizeof(float)));

    cudaMemcpy(d_x, inputData.back().data(), input_size * sizeof(float), cudaMemcpyHostToDevice);

    forward_pass<<<1, hidden_size>>>(d_x, y_pred, d_input_hidden_weights, d_hidden_output_weights, d_hidden_bias, d_output_bias, hidden_layer_output);
    // CUDA_CALL(cudaPeekAtLastError());
    CUDA_CALL(cudaDeviceSynchronize());

    CUDA_CALL(cudaMemcpy(h_output.data(), y_pred, output_size * sizeof(float), cudaMemcpyDeviceToHost));

    int max_idx = std::distance(h_output.begin(), std::max_element(h_output.begin(), h_output.end()));
    char predicted_char = (max_idx == input_size - 1) ? ' ' : 'a' + max_idx;

    cudaFree(d_x);
    cudaFree(y_pred);
    cudaFree(hidden_layer_output);

    return std::string(1, predicted_char);
}

int main()
{
    float *d_input_hidden_weights, *d_hidden_output_weights, *d_hidden_bias, *d_output_bias;

    initializeWeightsAndBiases(&d_input_hidden_weights, input_size * hidden_size);
    initializeWeightsAndBiases(&d_hidden_output_weights, hidden_size * output_size);
    initializeWeightsAndBiases(&d_hidden_bias, hidden_size);
    initializeWeightsAndBiases(&d_output_bias, output_size);

    std::string training_data = "hello, lorem ipsum dolor sit amet consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.";
    auto inputData = stringToInputData(training_data);

    printWeightsAndBiases(d_hidden_output_weights, hidden_size, output_size, "Hidden to Output Weights");
    for (int i = 0; i < inputData.size() - 1; i++)
    {
        train(inputData[i].data(), inputData[i + 1].data(), d_input_hidden_weights, d_hidden_output_weights, d_hidden_bias, d_output_bias);
    }
    // After training
    std::cout << "\nAfter Training:" << std::endl;
    CUDA_CALL(cudaDeviceSynchronize());
    printWeightsAndBiases(d_hidden_output_weights, hidden_size, output_size, "Hidden to Output Weights");

    // User interaction loop
    while (true)
    {
        std::string input_str;
        std::cout << "Enter string (or 'exit' to quit): ";
        std::getline(std::cin, input_str);
        if (input_str == "exit")
            break;
        if (input_str == "")
            continue;

        std::string predicted_str = predict(input_str, d_input_hidden_weights, d_hidden_output_weights, d_hidden_bias, d_output_bias);
        std::cout << "Predicted next character: " << predicted_str << std::endl;
    }

    CUDA_CALL(cudaFree(d_input_hidden_weights));
    CUDA_CALL(cudaFree(d_hidden_output_weights));
    CUDA_CALL(cudaFree(d_hidden_bias));
    CUDA_CALL(cudaFree(d_output_bias));

    return 0;
}