
from config import paths
from schema.data_schema import load_json_data_schema, save_schema
from config import paths
from utils import (
    set_seeds,
    read_csv_in_directory,
    split_train_val,
    read_json_as_dict
)
from preprocessing.preprocess import (
    train_pipeline_and_target_encoder,
    transform_data,
    save_pipeline_and_target_encoder,
    handle_class_imbalance
)
from prediction.predictor_model import (
    train_predictor_model,
    evaluate_predictor_model,
    save_predictor_model
)


def run_training(
        input_schema_dir: str = paths.INPUT_SCHEMA_DIR,
        saved_schema_path: str = paths.SAVED_SCHEMA_PATH,
        model_config_file_path: str = paths.MODEL_CONFIG_FILE_PATH,
        train_dir: str = paths.TRAIN_DIR,
        pipeline_config_file_path: str = paths.PREPROCESSING_CONFIG_FILE_PATH,
        pipeline_file_path: str = paths.PIPELINE_FILE_PATH,
        target_encoder_file_path: str = paths.TARGET_ENCODER_FILE_PATH,
        predictor_file_path: str = paths.PREDICTOR_FILE_PATH,
        default_hyperparameters_file_path: str = paths.DEFAULT_HYPERPARAMETERS_FILE_PATH) -> None:
    """
    Run the training process and saves model artifacts

    Args:
        input_schema_dir (str, optional): The directory path of the input schema.
        saved_schema_path (str, optional): The path where to save the schema.
        model_config_file_path (str, optional): The path of the model configuration file.
        train_dir (str, optional): The directory path of the train data.
        pipeline_config_file_path (str, optional): The path of the preprocessing configuration file.
        pipeline_file_path (str, optional): The path where to save the pipeline.
        target_encoder_file_path (str, optional): The path where to save the target encoder.
        predictor_file_path (str, optional): The path where to save the predictor model.
        default_hyperparameters_file_path (str, optional): The path of the default hyperparameters file.
        
    Returns:
        None
    """
    # load and save schema
    data_schema = load_json_data_schema(input_schema_dir)
    save_schema(schema=data_schema, output_path=saved_schema_path)

    # load model config
    model_config = read_json_as_dict(model_config_file_path)
    set_seeds(seed_value=model_config["seed_value"])

    # load train data
    train_data = read_csv_in_directory(file_dir_path=train_dir)

    # split train data into training and validation sets
    train_split, val_split = split_train_val(
        train_data, val_pct=model_config["validation_split"])

    # fit and transform using pipeline and target encoder, then save them
    pipeline, target_encoder = train_pipeline_and_target_encoder(
        data_schema, train_split, pipeline_config_file_path)
    transformed_train_inputs, transformed_train_targets = transform_data(
        pipeline, target_encoder, train_split)
    transformed_val_inputs, transformed_val_labels = transform_data(
        pipeline, target_encoder, val_split)
    balanced_train_inputs, balanced_train_labels = \
        handle_class_imbalance(transformed_train_inputs,
                               transformed_train_targets)
    save_pipeline_and_target_encoder(
        pipeline, target_encoder,
        pipeline_file_path,
        target_encoder_file_path)

    # uses default hyperparameters to train model
    default_hyperparameters = read_json_as_dict(default_hyperparameters_file_path)
    predictor = train_predictor_model(
        balanced_train_inputs, balanced_train_labels, default_hyperparameters)
    
    # save predictor model
    save_predictor_model(predictor, predictor_file_path)

    # calculate and print validation accuracy
    val_accuracy = evaluate_predictor_model(
        predictor, transformed_val_inputs, transformed_val_labels)
    print("Validation accuracy:", round(val_accuracy, 3))

    print("Training completed successfully")


if __name__ == "__main__":
    run_training()
