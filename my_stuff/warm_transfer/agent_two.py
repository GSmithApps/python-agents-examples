"""
This is the second agent. It was made to be transferred into with a cold call

- Has an agent name: test-agent-2

I think the trunk has this one answer if the call is to the LK number (+12402123203) (rather than the twilio
number, which is +17248061667). I'm thinking a call can come in from any number, but if not,
it would be configured to be my own phone number
"""

import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, inference, AgentServer, cli
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("listen-and-respond")
logger.setLevel(logging.INFO)

class ListenAndRespondAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent -- you're a supervisor (Please always remind the user of this when you talk to them).
                
                The calls you receive will be escalations from the first agent.
                The person you will initially talk to is the first agent -- they will
                give you information about the user who is calling.
                Please gather info from them if they have any. Then when there is no
                more info to gather from the first agent, they will
                connect you to the user, and you can talk to them.
                
                When the user speaks, you listen and respond.

            """
        )

    async def on_enter(self):
        
        self.session.generate_reply()

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session(agent_name="test-agent-2")
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

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
