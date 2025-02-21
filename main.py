import os
import torch
import gymnasium as gym
import cv2
from stable_baselines3 import DQN
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import EvalCallback, CallbackList
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.monitor import Monitor

from envs.discrete_car_racing import DiscreteCarRacing
from utils.callback import RenderCallback


def main():
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"

    # Create environment
    env = gym.make("CarRacing-v2", render_mode="rgb_array")
    # Convert environment to DiscreteCarRacing
    env = DiscreteCarRacing(env)

    # Check environment
    check_env(env)

    # Monitor environment
    env = Monitor(env)
    # Wrap environment
    env = DummyVecEnv([lambda: env])

    # Initialize device
    if torch.cuda.is_available():
        device = torch.device("cuda:0")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    # Create model
    model = DQN(
        "CnnPolicy",
        env,
        verbose=1,
        buffer_size=1000000,
        learning_starts=50000,
        batch_size=4096,
        gamma=0.99,
        train_freq=4,
        target_update_interval=5000,
        exploration_fraction=0.1,
        exploration_final_eps=0.02,
        learning_rate=1e-4,
        tensorboard_log="./tf-logs/",
        device=device,
    )

    # Create EvalCallback to evaluate the model and save the best one
    eval_callback = EvalCallback(
        env,
        best_model_save_path="./models/",
        log_path="./logs/",
        eval_freq=1000,
        deterministic=True,
        render=False,
    )

    # Create RenderCallback to render the environment
    render_callback = RenderCallback(render_freq=5000)

    # Create CallbackList
    callback = CallbackList([eval_callback, render_callback])

    # Train model
    model.learn(total_timesteps=5000000, callback=callback)

    # Save model
    model.save("./models/final_model")

    # Load final model
    model = DQN.load("./models/final_model", env=env)

    # Render final model to video
    obs = env.reset()
    os.makedirs("./rendered_videos", exist_ok=True)
    video_writer = cv2.VideoWriter(
        "./rendered_videos/car_racing_final_model.avi",
        cv2.VideoWriter_fourcc(*"MJPG"),
        30,
        (env.render().shape[1], env.render().shape[0]),
    )

    for _ in range(1000):
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, dones, info = env.step(action)
        frame = env.render()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Convert RGB to BGR
        video_writer.write(frame)
        if dones:
            obs = env.reset()

    video_writer.release()
    env.close()


if __name__ == "__main__":
    main()
