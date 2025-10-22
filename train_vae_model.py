"""
TRAINING SCRIPT - Variational AutoEncoder (VAE) para mejoras educativas
Genera mejoras sintéticas basadas en la distribución de datos reales

Uso:
    python train_vae_model.py --data data.csv --epochs 50
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# TensorFlow/Keras imports
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Reducir logs
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, Model, backend as K
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    print("✓ TensorFlow/Keras disponible")
except ImportError:
    print("✗ TensorFlow no disponible. Instala: pip install tensorflow>=2.10.0")
    sys.exit(1)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurar GPU si está disponible
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    logger.info(f"✓ GPUs detectadas: {len(gpus)}")
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)


class VAETrainer:
    """Entrena un Variational AutoEncoder"""
    
    def __init__(self, latent_dim=8, input_dim=14):
        """
        latent_dim: Dimensión del espacio latente
        input_dim: Número de features de entrada
        """
        self.latent_dim = latent_dim
        self.input_dim = input_dim
        self.encoder = None
        self.decoder = None
        self.vae = None
        self.scaler = StandardScaler()
        logger.info(f"✓ VAETrainer inicializado (input_dim={input_dim}, latent_dim={latent_dim})")
    
    def _sampling(self, args):
        """Sampling layer del VAE"""
        z_mean, z_log_var = args
        batch = K.shape(z_mean)[0]
        dim = K.int_shape(z_mean)[1]
        epsilon = K.random_normal(shape=(batch, dim))
        return z_mean + K.exp(0.5 * z_log_var) * epsilon
    
    def build_vae(self):
        """Construye la arquitectura VAE"""
        logger.info("Construyendo arquitectura VAE...")
        
        # ============ ENCODER ============
        encoder_input = keras.Input(shape=(self.input_dim,), name='encoder_input')
        
        # Encoder: capas densas con regularización
        x = layers.Dense(64, activation='relu', name='encoder_dense_1')(encoder_input)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
        
        x = layers.Dense(32, activation='relu', name='encoder_dense_2')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
        
        x = layers.Dense(16, activation='relu', name='encoder_dense_3')(x)
        
        # Latent space
        z_mean = layers.Dense(self.latent_dim, name='z_mean')(x)
        z_log_var = layers.Dense(self.latent_dim, name='z_log_var')(x)
        
        # Sampling
        z = layers.Lambda(self._sampling, output_shape=(self.latent_dim,),
                         name='z')([z_mean, z_log_var])
        
        # Encoder model
        self.encoder = Model(encoder_input, [z_mean, z_log_var, z], name='encoder')
        self.encoder.summary()
        
        # ============ DECODER ============
        latent_input = keras.Input(shape=(self.latent_dim,), name='z_sampling')
        
        x = layers.Dense(16, activation='relu', name='decoder_dense_1')(latent_input)
        x = layers.Dense(32, activation='relu', name='decoder_dense_2')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
        
        x = layers.Dense(64, activation='relu', name='decoder_dense_3')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
        
        # Output: valores entre -1 y 1 (escalados después)
        decoder_output = layers.Dense(self.input_dim, activation='linear',
                                     name='decoder_output')(x)
        
        # Decoder model
        self.decoder = Model(latent_input, decoder_output, name='decoder')
        self.decoder.summary()
        
        # ============ VAE COMPLETO ============
        outputs = self.decoder(self.encoder(encoder_input)[2])
        self.vae = Model(encoder_input, outputs, name='vae')
        
        # Loss personalizado: ELBO (Evidence Lower Bound)
        def vae_loss(x_true, x_pred):
            # Reconstruction loss
            recon_loss = keras.losses.mean_squared_error(x_true, x_pred)
            recon_loss *= self.input_dim
            
            # KL divergence loss
            kl_loss = 1 + z_log_var - K.square(z_mean) - K.exp(z_log_var)
            kl_loss = K.sum(kl_loss, axis=-1)
            kl_loss *= -0.5
            
            return K.mean(recon_loss + kl_loss)
        
        self.vae.compile(optimizer=keras.optimizers.Adam(learning_rate=1e-3),
                        loss=vae_loss)
        
        logger.info("✓ VAE compilado correctamente")
        return self.vae
    
    def train(self, X_train, X_val, epochs=50, batch_size=32, verbose=1):
        """
        Entrena el VAE
        
        Args:
            X_train: Datos de entrenamiento
            X_val: Datos de validación
            epochs: Número de épocas
            batch_size: Tamaño del batch
            verbose: Verbosidad del entrenamiento
        
        Returns:
            history del entrenamiento
        """
        logger.info(f"Iniciando entrenamiento por {epochs} épocas...")
        
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True,
                verbose=1
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-5,
                verbose=1
            )
        ]
        
        history = self.vae.fit(
            X_train, X_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_val, X_val),
            callbacks=callbacks,
            verbose=verbose
        )
        
        logger.info("✓ Entrenamiento completado")
        return history
    
    def save_models(self, output_dir='PROYECTO SIUUU/models'):
        """Guarda encoder, decoder y scaler"""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Guardar encoder
        encoder_path = output_path / 'vae_encoder.h5'
        self.encoder.save(str(encoder_path))
        logger.info(f"✓ Encoder guardado: {encoder_path}")
        
        # Guardar decoder
        decoder_path = output_path / 'vae_decoder.h5'
        self.decoder.save(str(decoder_path))
        logger.info(f"✓ Decoder guardado: {decoder_path}")
        
        # Guardar scaler
        import joblib
        scaler_path = output_path / 'vae_scaler.pkl'
        joblib.dump(self.scaler, str(scaler_path))
        logger.info(f"✓ Scaler guardado: {scaler_path}")
        
        # Guardar metadata
        metadata = {
            'latent_dim': self.latent_dim,
            'input_dim': self.input_dim,
            'scaler_mean': self.scaler.mean_.tolist(),
            'scaler_std': self.scaler.scale_.tolist(),
            'created_at': pd.Timestamp.now().isoformat()
        }
        metadata_path = output_path / 'vae_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"✓ Metadata guardado: {metadata_path}")
        
        return {
            'encoder': str(encoder_path),
            'decoder': str(decoder_path),
            'scaler': str(scaler_path),
            'metadata': str(metadata_path)
        }
    
    @classmethod
    def load_models(cls, output_dir='PROYECTO SIUUU/models'):
        """Carga modelos entrenados"""
        
        output_path = Path(output_dir)
        
        # Cargar encoder
        encoder_path = output_path / 'vae_encoder.h5'
        encoder = keras.models.load_model(str(encoder_path))
        logger.info(f"✓ Encoder cargado: {encoder_path}")
        
        # Cargar decoder
        decoder_path = output_path / 'vae_decoder.h5'
        decoder = keras.models.load_model(str(decoder_path))
        logger.info(f"✓ Decoder cargado: {decoder_path}")
        
        # Cargar scaler
        import joblib
        scaler_path = output_path / 'vae_scaler.pkl'
        scaler = joblib.load(str(scaler_path))
        logger.info(f"✓ Scaler cargado: {scaler_path}")
        
        # Cargar metadata
        metadata_path = output_path / 'vae_metadata.json'
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        logger.info(f"✓ Metadata cargado: {metadata_path}")
        
        return encoder, decoder, scaler, metadata


def load_and_prepare_data(data_path, features=None, test_size=0.2):
    """
    Carga y prepara datos para entrenamiento
    
    Args:
        data_path: Ruta del dataset
        features: Lista de columnas a usar (None = automático)
        test_size: Proporción de validación
    
    Returns:
        X_train, X_val escalados
    """
    
    logger.info(f"Cargando datos desde: {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Dataset cargado: {df.shape}")
    
    # Features por defecto (14 features estándar)
    if features is None:
        features = [
            'poblacion_total', 'porcentaje_rural', 'estrato_promedio',
            'tasa_pobreza', 'num_instituciones', 'computadores_por_estudiante',
            'salones_por_institucion', 'docentes_por_institucion',
            'cobertura_electrica', 'cobertura_4g',
            'dispositivos_promedio_hogar', 'tasa_aprobacion',
            'tasa_desercion', 'puntaje_pruebas'
        ]
    
    # Verificar que existan todas las features
    missing = [f for f in features if f not in df.columns]
    if missing:
        logger.warning(f"Features no encontradas: {missing}")
        logger.info(f"Columnas disponibles: {df.columns.tolist()}")
        raise ValueError(f"Features faltantes: {missing}")
    
    X = df[features].copy()
    
    # Limpiar datos
    X = X.fillna(X.mean())  # Llenar NaN con media
    X = X[(X >= 0).all(axis=1)]  # Eliminar valores negativos
    
    logger.info(f"Datos limpios: {X.shape}")
    logger.info(f"Features: {features}")
    
    # Dividir datos
    X_train, X_val = train_test_split(X, test_size=test_size, random_state=42)
    logger.info(f"Train: {X_train.shape}, Val: {X_val.shape}")
    
    # Escalar
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    return X_train_scaled, X_val_scaled, scaler, features


def main():
    """Función principal"""
    
    parser = argparse.ArgumentParser(
        description='Entrenar VAE para generación de mejoras educativas'
    )
    parser.add_argument(
        '--data',
        type=str,
        default='PROYECTO SIUUU/data/processed/education_dataset.csv',
        help='Ruta del dataset'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=50,
        help='Número de épocas de entrenamiento'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Tamaño del batch'
    )
    parser.add_argument(
        '--latent-dim',
        type=int,
        default=8,
        help='Dimensión del espacio latente'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='PROYECTO SIUUU/models',
        help='Directorio de salida'
    )
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("VAE TRAINING - Generación de Mejoras Educativas")
    logger.info("="*60)
    
    try:
        # 1. Cargar datos
        X_train, X_val, scaler, features = load_and_prepare_data(
            args.data
        )
        
        # 2. Crear y entrenar VAE
        trainer = VAETrainer(
            latent_dim=args.latent_dim,
            input_dim=len(features)
        )
        trainer.scaler = scaler
        trainer.build_vae()
        
        # 3. Entrenar
        history = trainer.train(
            X_train, X_val,
            epochs=args.epochs,
            batch_size=args.batch_size
        )
        
        # 4. Guardar modelos
        paths = trainer.save_models(args.output_dir)
        
        logger.info("\n✓ VAE TRAINING COMPLETADO")
        logger.info(f"Modelos guardados en: {args.output_dir}")
        logger.info(f"Encoder: {paths['encoder']}")
        logger.info(f"Decoder: {paths['decoder']}")
        logger.info(f"Scaler: {paths['scaler']}")
        logger.info(f"Metadata: {paths['metadata']}")
        
    except FileNotFoundError as e:
        logger.error(f"✗ Archivo no encontrado: {e}")
        logger.info("Creando datos sintéticos para demostración...")
        
        # Crear datos sintéticos para demostración
        n_samples = 1000
        n_features = 14
        X = np.random.normal(50, 20, (n_samples, n_features)).clip(0, 100)
        X_train, X_val = train_test_split(X, test_size=0.2, random_state=42)
        
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_val = scaler.transform(X_val)
        
        # Entrenar con datos sintéticos
        trainer = VAETrainer(latent_dim=args.latent_dim, input_dim=n_features)
        trainer.scaler = scaler
        trainer.build_vae()
        history = trainer.train(X_train, X_val, epochs=args.epochs)
        paths = trainer.save_models(args.output_dir)
        
        logger.info("✓ VAE entrenado con datos sintéticos")
        logger.info(f"Modelos guardados en: {args.output_dir}")


if __name__ == '__main__':
    main()
