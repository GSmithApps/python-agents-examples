"""

This is the first agent. It was made to be transferred out of with a cold call

- Has an agent name: test-agent

I think the trunk has this one answer if the call is to the twilio number (+17248061667) rather than the LK number (+12402123203).
I'm thinking a call can come in from any number, but if not,
it would be configured to be my own phone number
"""

import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, inference, AgentServer, cli
from livekit.plugins import silero

from livekit import api
from livekit.agents.beta.workflows import WarmTransferTask

from asyncio import sleep

from my_stuff.my_utils import MyLogger
from livekit.agents.llm import ToolError, function_tool


load_dotenv()

logger = logging.getLogger("listen-and-respond")
logger.setLevel(logging.INFO)

my_logger = MyLogger(logger)

SUMMARY_INSTRUCTIONS = """
Introduce the conversation from your perspective as the AI assistant who participated in this call:

WHO you're talking to (name, role, company if mentioned)
WHY they contacted you (goal, problem, request)
WHY a supervisor is requested or needed at this point
Brief summary in 100-200 characters from a first-person perspective"""

class ListenAndRespondAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
                You are the first agent. Please always remind the user of this when you talk to them

                # Transferring to a supervisor

                In some cases, the user may ask to speak to a supervisor. This could happen when you are unable to answer their question.
            """
        )

    async def on_enter(self):
        
        self.session.generate_reply()


    @function_tool
    async def transfer_to_supervisor(self) -> None:
        """Called when the user asks to speak to a supervisor. This will put the user on
           hold while the supervisor is connected.

        Examples on when the tool should be called:
        ----
        - User: Can I speak to your supervisor?
        - Assistant: Yes of course.
        ----
        - Assistant: I'm unable to help with that, would you like to speak to a supervisor?
        - User: Yes please.
        ----
        """

        SUPERVISOR_PHONE_NUMBER = '+12402123203'

        my_logger.info("tool called to transfer to supervisor")
        await self.session.say(
            "Please hold while I connect you to a supervisor.", allow_interruptions=False
        )
        try:

            result = await WarmTransferTask(
                sip_call_to=SUPERVISOR_PHONE_NUMBER,
                sip_trunk_id="ST_EfLWk22seka5",
                # caller ID shown to the supervisor; must be a number on the trunk above
                sip_number="+17248061667",
                chat_ctx=self.chat_ctx,
                # to reach an extension behind an IVR, pass DTMF tones to send once
                # answered, e.g. dtmf="wwww1234#" (each `w` pauses ~0.5s):
                # dtmf=SUPERVISOR_EXTENSION,
                # give up if the supervisor doesn't pick up within 25s:
                # ringing_timeout=25,
                # add extra instructions for summarization
                # you can also customize the entire instructions by overriding the `get_instructions` method
                extra_instructions=SUMMARY_INSTRUCTIONS,
            )

        except ToolError as e:
            my_logger.info(f"failed to transfer to supervisor with tool error: {e}")
            raise e

        my_logger.info(
            "transfer to supervisor successful",
        )
        # await self.session.say(
        #     "you are on the line with my supervisor. I'll be hanging up now.",
        #     allow_interruptions=False,
        # )
        self.session.shutdown()


server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session(agent_name="test-agent")
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    agent = ListenAndRespondAgent()

    ctx.room.name

    

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
