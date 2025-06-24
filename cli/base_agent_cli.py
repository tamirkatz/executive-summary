import argparse
import json
from backend.agents.base_agent import BaseAgent


def main():
    parser = argparse.ArgumentParser(description='Test BaseAgent behavior.')
    parser.add_argument('--agent_type', type=str, required=True, help='Type of the agent')
    parser.add_argument('--state', type=str, required=True, help='JSON string representing the state')
    parser.add_argument('--status', type=str, help='Status message to send')
    parser.add_argument('--error_msg', type=str, help='Error message to send')
    parser.add_argument('--step', type=str, help='Step at which error occurred')
    parser.add_argument('--continue_research', type=bool, default=True, help='Flag to continue research after error')

    args = parser.parse_args()

    # Parse the state JSON string
    state = json.loads(args.state)

    # Initialize the BaseAgent
    agent = BaseAgent(agent_type=args.agent_type)

    # Log agent start
    agent.log_agent_start(state)

    # Send status or error update based on provided arguments
    if args.status:
        websocket_manager, job_id = agent.get_websocket_info(state)
        agent.send_status_update(websocket_manager, job_id, args.status)
    elif args.error_msg:
        websocket_manager, job_id = agent.get_websocket_info(state)
        agent.send_error_update(websocket_manager, job_id, args.error_msg, args.step, args.continue_research)

    # Log agent completion
    agent.log_agent_complete(state)


if __name__ == '__main__':
    main() 