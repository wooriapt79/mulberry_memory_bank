
import os
import sys
import json
import random

# Add the root directory to sys.path to find marrf module
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from marrf.synapse_capture_protocol import SynapseCaptureProtocol, plot_scp_dashboard # Import plot_scp_dashboard
import datetime

def random_strategy(scp_engine: SynapseCaptureProtocol, num_steps: int = 10):
    """Simulates SCP with random triggers and resets."""
    metrics_history = []
    user_empathy_history = []

    print("--- Simulating SCP states with Random Strategy ---")
    for i in range(num_steps):
        print(f"\nCycle {i+1}:")
        if random.random() > 0.5:
            level = random.uniform(0.1, 1.0)
            scp_engine.trigger_protocol(level)
        else:
            scp_engine.reset_protocol()

        print(f"Bio Message: {scp_engine.generate_bio_message()}")
        print(f"Response: {scp_engine.response_controller('오늘의 날씨는?')}")

        metrics_history.append(scp_engine.metrics['cognitive_load'])
        user_empathy_history.append(random.uniform(0.3, 0.9) if scp_engine.is_protocol_active else random.uniform(0.7, 1.0))
    return metrics_history, user_empathy_history

def gradual_load_increase_strategy(scp_engine: SynapseCaptureProtocol, num_steps: int = 10):
    """Simulates SCP with gradually increasing cognitive load."""
    metrics_history = []
    user_empathy_history = []

    print("--- Simulating SCP states with Gradual Load Increase Strategy ---")
    for i in range(num_steps):
        print(f"\nCycle {i+1}:")
        load_level = (i + 1) / num_steps # Gradually increase load from ~0.1 to 1.0
        scp_engine.trigger_protocol(load_level)

        print(f"Bio Message: {scp_engine.generate_bio_message()}")
        print(f"Response: {scp_engine.response_controller('처리할 데이터가 많습니다.')}")

        metrics_history.append(scp_engine.metrics['cognitive_load'])
        user_empathy_history.append(random.uniform(0.3, 0.7) if scp_engine.metrics['cognitive_load'] > 0.5 else random.uniform(0.7, 1.0))
    return metrics_history, user_empathy_history

def intermittent_burst_stress_strategy(scp_engine: SynapseCaptureProtocol, num_steps: int = 10):
    """Simulates SCP with short bursts of high stress followed by recovery periods."""
    metrics_history = []
    user_empathy_history = []

    print("-- Simulating SCP states with Intermittent Burst Stress Strategy ---")
    for i in range(num_steps):
        print(f"\nCycle {i+1}:")
        if (i % 3) == 0: # Every 3rd cycle, trigger high stress
            level = random.uniform(0.7, 1.0)
            scp_engine.trigger_protocol(level)
        else: # Otherwise, allow for recovery
            scp_engine.reset_protocol()

        print(f"Bio Message: {scp_engine.generate_bio_message()}")
        print(f"Response: {scp_engine.response_controller('긴급 보고서 준비')}")

        metrics_history.append(scp_engine.metrics['cognitive_load'])
        user_empathy_history.append(random.uniform(0.2, 0.6) if scp_engine.is_protocol_active else random.uniform(0.8, 1.0))
    return metrics_history, user_empathy_history

def run_simulation(strategy_name: str, num_steps: int = 10):
    """Runs a SCP simulation based on the specified strategy."""
    scp_engine = SynapseCaptureProtocol()
    metrics_history = []
    user_empathy_history = []

    if strategy_name == 'random':
        metrics_history, user_empathy_history = random_strategy(scp_engine, num_steps)
    elif strategy_name == 'gradual_load_increase':
        metrics_history, user_empathy_history = gradual_load_increase_strategy(scp_engine, num_steps)
    elif strategy_name == 'intermittent_burst_stress':
        metrics_history, user_empathy_history = intermittent_burst_stress_strategy(scp_engine, num_steps)
    else:
        print(f"Error: Unknown strategy '{strategy_name}'. Running random strategy instead.")
        metrics_history, user_empathy_history = random_strategy(scp_engine, num_steps)

    # Save research data
    research_data = {
        "timestamp": str(datetime.datetime.now()),
        "strategy": strategy_name,
        "metrics_history": metrics_history,
        "user_empathy_history": user_empathy_history
    }

    output_filename = f'research_log_{strategy_name}.json'
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(research_data, f, indent=4)

    with open('agent_activity.md', 'a', encoding='utf-8') as f:
        f.write(f"\n\n### SCP Simulation Log - {datetime.date.today()} ({strategy_name.replace('_', ' ').title()} Strategy)\n")
        f.write(f"- Final Cognitive Load: {scp_engine.metrics['cognitive_load']:.2f}\n")
        f.write(f"- Protocol Active: {scp_engine.is_protocol_active}\n")

    print(f"✅ SCP simulation data saved to {output_filename} and agent_activity.md")
    print("\n--- Plotting SCP Dashboard ---")
    plot_scp_dashboard(metrics_history, user_empathy_history)
    print("✅ SCP simulation and dashboard plotting complete.")

if __name__ == '__main__':
    # Example usage: run with a specific strategy
    # You can change 'random' to 'gradual_load_increase' or 'intermittent_burst_stress'
    selected_strategy = os.getenv('SCP_STRATEGY', 'random')
    print(f"Running SCP simulation with strategy: {selected_strategy.replace('_', ' ').title()}")
    run_simulation(selected_strategy, num_steps=10)
