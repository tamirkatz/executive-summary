import argparse
import json
from backend.agents.role_router import RoleRelevanceRouterNode


def main():
    parser = argparse.ArgumentParser(description='Test RoleRelevanceRouterNode behavior.')
    parser.add_argument('--state', type=str, required=True, help='JSON string representing the state')

    args = parser.parse_args()

    # Parse the state JSON string
    state = json.loads(args.state)

    # Initialize the RoleRelevanceRouterNode
    router_node = RoleRelevanceRouterNode()

    # Call the router node with the state
    result = router_node(state)

    # Print the result
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main() 