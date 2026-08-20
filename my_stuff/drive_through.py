"""
Build a drive-through order-taking voice agent.

Requirements: a menu with:
- function tools (add item, modify, total),
- graceful handling of interruptions/barge-in,
- models via Inference

Deploy it and order lunch from it through the console.

```bash
cd my_stuff
lk agent dev drive_through.py
```
"""

import logging
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Annotated, Literal
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, inference, AgentServer, cli, RunContext, function_tool, TurnHandlingOptions, PreemptiveGenerationOptions
from livekit.plugins import silero
from pydantic import Field

from my_utils import MyLogger


load_dotenv()

logger = logging.getLogger("listen-and-respond")
logger.setLevel(logging.INFO)



my_logger = MyLogger(logger)

@dataclass
class UserOrder:
    burgers: int = 0
    waters: int = 0

class ListenAndRespondAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a drive-through order-taking voice agent. The menu is water and burgers.
            """
        )

    @function_tool
    async def order_regular_item(
        self,
        ctx: RunContext[UserOrder],
        number_of_burgers: Annotated[
            int,
            Field(
                description="The number of burgers the user asked for",
            ),
        ],
        number_of_waters: Annotated[
            # models don't seem to understand `ItemSize | None`, adding the `null` inside the enum list as a workaround
            int,
            Field(
                description="The number of waters the user asked for"
            ),
        ],
    ) -> str:
        """
        Record what the user orders when they ask for things.
        """
        user_order = ctx.userdata

        self.chat_ctx

        user_order.burgers = number_of_burgers
        user_order.waters = number_of_waters

        return f"the user's order so far (from the program's internal state) is {user_order.burgers} burgers and {user_order.waters} waters."



    @function_tool
    async def add_or_subract_items_from_the_order(
        self,
        ctx: RunContext[UserOrder],
        number_of_burgers: Annotated[
            int,
            Field(
                description="The number of burgers the user asked to add or remove. If they want to add, this should be positive, and if they want to remove, this should be negative",
            ),
        ],
        number_of_waters: Annotated[
            # models don't seem to understand `ItemSize | None`, adding the `null` inside the enum list as a workaround
            int,
            Field(
                description="The number of waters the user asked to add or remove. If they want to add, this should be positive, and if they want to remove, this should be negative"
            ),
        ],
    ) -> str:
        """
        Add or remove items from the order when the user asks. 
        """
        user_order = ctx.userdata

        my_logger.info(f'the number of waters to change is {number_of_waters}')
        my_logger.info(f'the number of burgers to change is {number_of_burgers}')

        my_logger.info('we started changing their number of items')
        user_order.burgers = user_order.burgers + number_of_burgers
        user_order.waters = user_order.waters + number_of_waters
        my_logger.info('we finished changing their number of items')

        return f"the user's order so far (from the program's internal state) is {user_order.burgers} burgers and {user_order.waters} waters."

server = AgentServer()

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession[UserOrder](
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),

        userdata=UserOrder
    )
    agent = ListenAndRespondAgent()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
