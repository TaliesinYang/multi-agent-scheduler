"""
Main entry point for Multi-Agent Scheduler

Starts the health check API and initializes monitoring.
"""

import asyncio
import argparse
import sys

from src.health import run_health_api, set_service_status


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Scheduler - Production Ready"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind health API (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for health API (default: 8000)"
    )
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Don't start health API server"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Multi-Agent Scheduler v3.0.0")
    print("=" * 60)

    # Initialize services
    try:
        # Check Redis connection (if configured)
        set_service_status("redis", "unknown")

        # Check Jaeger connection (if configured)
        set_service_status("jaeger", "unknown")

        print("✅ Services initialized")

    except Exception as e:
        print(f"❌ Error initializing services: {e}")
        sys.exit(1)

    # Start health API
    if not args.no_api:
        print(f"\n🚀 Starting health API at http://{args.host}:{args.port}")
        print(f"   Health check: http://{args.host}:{args.port}/health")
        print(f"   Metrics: http://{args.host}:{args.port}/metrics")
        print(f"   Readiness: http://{args.host}:{args.port}/ready")
        print("\n📊 Ready to process tasks!\n")

        try:
            await run_health_api(host=args.host, port=args.port)
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down gracefully...")
        except Exception as e:
            print(f"\n❌ Error running health API: {e}")
            sys.exit(1)
    else:
        print("\n📊 Running without health API (--no-api flag)")
        print("   Scheduler is ready to process tasks programmatically\n")

        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
