"""
Main Game Script
This script implements a multi-agent game system with attackers and defenders.
It handles initialization, configuration, and the main game loop.
WARNING: Before edit, check out the Advanced Usage part of the documentation.
"""

# ------------------------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------------------------
import os
import sys
import pickle

# Import self defined libraries, auto fix path issues
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not root_dir.endswith("games"):
    current_file_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file_path)
    parent_dir = os.path.dirname(current_dir)
    root_dir = parent_dir
    sys.path.append(root_dir)

from lib.core import *
check_and_install_dependencies()
from lib.interface import *
from lib.utilities import *
import config as cfg
import attacker_strategy
import defender_strategy
from gamms.VisualizationEngine import Color

print(colored("Imported libraries successfully", "green"))
print("Root Directory: ", root_dir)


# ------------------------------------------------------------------------------
# Main Game Script
# ------------------------------------------------------------------------------
def main():
    # Record the time
    time = 0
    # Record the payoff
    payoff = 0

    try:

        # Check if the user wants to use the predefined game rules
        if cfg.GAME_RULE is not None:
            load_game_rule(cfg, cfg.GAME_RULE)

        # Sets up the basic game environment and loads the graph structure
        ctx, G = initialize_game_context(cfg.VISUALIZATION_ENGINE, cfg.GRAPH_PATH, cfg.LOCATION, cfg.RESOLUTION)

        # Create sensor systems for environment perception
        # These sensors allow agents to gather information about their environment
        ctx.sensor.create_sensor("map", cfg.MAP_SENSOR)
        ctx.sensor.create_sensor("agent", cfg.AGENT_SENSOR)
        ctx.sensor.create_sensor("neighbor", cfg.NEIGHBOR_SENSOR)

        # Extract the global parameters for the agents
        global_params = {
            # Attacker globals
            "attacker_sensors": cfg.ATTACKER_GLOBAL_SENSORS,
            "attacker_color": cfg.ATTACKER_GLOBAL_COLOR,
            "attacker_speed": cfg.ATTACKER_GLOBAL_SPEED,
            "attacker_capture_radius": cfg.ATTACKER_GLOBAL_CAPTURE_RADIUS,
            # Defender globals
            "defender_sensors": cfg.DEFENDER_GLOBAL_SENSORS,
            "defender_color": cfg.DEFENDER_GLOBAL_COLOR,
            "defender_speed": cfg.DEFENDER_GLOBAL_SPEED,
            "defender_capture_radius": cfg.DEFENDER_GLOBAL_CAPTURE_RADIUS,
        }

        # Configure agents with the organized parameters
        agent_config, agent_params_map = initialize_agents(ctx=ctx, attacker_config=cfg.ATTACKER_CONFIG, defender_config=cfg.DEFENDER_CONFIG, global_params=global_params)

        # Assign strategies to agents
        assign_strategies(ctx, agent_config, attacker_strategy, defender_strategy)

        # Configure visualization settings
        configure_visualization(
            ctx, agent_config, {"width": 1980, "height": 1080, "draw_node_id": cfg.DRAW_NODE_ID, "node_color": Color.Black, "edge_color": Color.Gray, "game_speed": cfg.GAME_SPEED, "default_color": Color.White, "default_size": cfg.GLOBAL_AGENT_SIZE}
        )

        # Initialize flags in the game environment
        initialize_flags(ctx, cfg.FLAG_POSITIONS, cfg.FLAG_SIZE, cfg.FLAG_COLOR)

        # Initialize the logger
        log_file = initialize_logger(current_dir)  # Ensure LOG_SAVE_PATH is defined in config

        # Main game loop
        while not ctx.is_terminated():
            time += 1
            # Process each agent's turn
            for agent in ctx.agent.create_iter():
                # Get current state and update with flag information
                state = agent.get_state()
                state.update({"flag_pos": cfg.FLAG_POSITIONS, "flag_weight": cfg.FLAG_WEIGHTS, "agent_params": agent_params_map.get(agent.name, {}), "time": time, "payoff": payoff})

                # Execute agent strategy or handle human input
                if hasattr(agent, "strategy") and agent.strategy is not None:
                    agent.strategy(state)
                else:
                    # Handle human-controlled agents
                    node = ctx.visual.human_input(agent.name, state)
                    state["action"] = node

                agent.set_state()

            # Check victory condition: all attackers captured
            still_has_attackers = any(agent.team == "attacker" for agent in ctx.agent.create_iter())
            if not still_has_attackers:
                print("All attackers have been captured")
                break

            # Update visualization and check agent interactions
            ctx.visual.simulate()
            captures, tags, attacker_count, defender_count = check_agent_interaction(ctx, G, agent_params_map, cfg.FLAG_POSITIONS, cfg.INTERACTION)
            if check_termination(time, cfg.MAX_TIME, attacker_count, defender_count):
                break
            payoff = compute_payoff(cfg.PAYOFF, captures, tags)

            # Prepare agent positions for logging
            active_agents = list(ctx.agent.create_iter())  # Convert iterator to list for multiple passes
            agent_positions = create_game_log_entry(agent_params_map, active_agents)

            # Log the current game step
            log_game_step(log_file, time, payoff, agent_positions)

        # After the loop ends, finalize the log
        finalize_logger(log_file)
    except KeyboardInterrupt:
        print(colored("Game interrupted by user. Cleaning up...", "yellow"))
        # Handle clean exit when Ctrl+C is pressed
        try:
            if log_file:
                # Log final state before exit
                active_agents = list(ctx.agent.create_iter())
                agent_positions = create_game_log_entry(agent_params_map, active_agents)
                log_game_step(log_file, time, payoff, agent_positions, is_last=True)
                print(colored("Final game state logged successfully", "green"))
        except Exception as e:
            print(colored(f"Error during cleanup: {e}", "red"))

    except Exception as e:
        print(colored(f"An error occurred: {e}", "red"))
        # Handle other exceptions as before
        try:
            if log_file:
                active_agents = list(ctx.agent.create_iter())
                agent_positions = create_game_log_entry(agent_params_map, active_agents)
                log_game_step(log_file, time, payoff, agent_positions, is_last=True)
        except Exception as inner_e:
            print(colored(f"Failed to log the final game step: {inner_e}", "red"))

    finally:
        print(colored("Game completed successfully", "green"))
        # Ensure logger is always finalized
        if log_file:
            finalize_logger(log_file)


if __name__ == "__main__":
    main()
