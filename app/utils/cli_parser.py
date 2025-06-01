# utils/cli_parser.py

import sys

def print_log(ids, msg):
    print(f"[Party {ids}] {msg}", flush=True)

def print_usage_and_exit():
    print(f"Usage: python mpyc_task.py [MPyC options] <dataset.csv>", end=" ")
    print("[--regression-type|--r] [linear|logistic]", end=" ")
    print("[--lr] <learning_rate> [--epochs] <num_epochs>", end=" ")
    print("[--normalizer|--n] [minmax|zscore] [--label] <label_name> [--help|-h]")

    print("\nArguments:")
    print("  [MPyC options]     : Optional, like -M (number of parties) or -I (party id)")
    print("  <dataset.csv>      : Path to the local party's CSV file")
    print("  --normalizer -n    : Choose normalization method: 'minmax' or 'zscore', default to none")
    print("  --regression -r    : Choose regression method: 'linear' or 'logistic', default to 'linear'")
    print("  --lr               : Learning rate for training (float), optional")
    print("  --epochs           : Number of epochs for training (int), optional")
    print("  --label            : Target label column name, with fallback detection if not found")
    print("  --help -h          : Show this help message and exit")

    print("\nExample:")
    for i in range(3):
        example = f"  python mpyc_task.py -M3 -I{i} party{i}_data.csv -n zscore -r logistic --lr 0.1 --epochs 100"
        print(example)
    
    print()
    sys.exit(1)

def parse_cli_args():
    if '--help' in sys.argv or '-h' in sys.argv:
        print_usage_and_exit()

    if len(sys.argv) < 2:
        print_usage_and_exit()

    csv_file = None
    normalizer_type = None
    regression_type = "linear"
    learning_rate = None
    epochs = None
    label_name = None
    is_logging = '--verbose' in sys.argv or '--debug' in sys.argv

    # Extract CSV file
    for arg in sys.argv[1:]:
        if not arg.startswith("-") and csv_file is None:
            csv_file = arg

    if csv_file is None:
        print("❌ CSV file not provided.\n")
        print_usage_and_exit()

    def get_arg_value(flags):
        for flag in flags:
            if flag in sys.argv:
                idx = sys.argv.index(flag)
                if idx + 1 < len(sys.argv):
                    return sys.argv[idx + 1]
        return None

    # Parse optional arguments
    normalizer_type = get_arg_value(['--normalizer', '-n'])
    regression_type = get_arg_value(['--regression-type', '-r']) or "linear"
    lr_str = get_arg_value(['--lr'])
    epochs_str = get_arg_value(['--epochs'])
    label_name = get_arg_value(['--label'])

    # Convert and validate lr and epochs
    if lr_str:
        try:
            learning_rate = float(lr_str)
        except ValueError:
            print("❌ Invalid learning rate. Must be a float.\n")
            print_usage_and_exit()

    if epochs_str:
        try:
            epochs = int(epochs_str)
        except ValueError:
            print("❌ Invalid number of epochs. Must be an integer.\n")
            print_usage_and_exit()

    return {
        "csv_file": csv_file,
        "normalizer_type": normalizer_type,
        "regression_type": regression_type,
        "learning_rate": learning_rate,
        "epochs": epochs,
        "label_name": label_name,
        "is_logging": is_logging
    }
