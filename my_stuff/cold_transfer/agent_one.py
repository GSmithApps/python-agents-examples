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

from asyncio import sleep

from my_stuff.my_utils import MyLogger


load_dotenv()

logger = logging.getLogger("listen-and-respond")
logger.setLevel(logging.INFO)

my_logger = MyLogger(logger)

async def transfer_call(participant_identity: str, room_name: str) -> None:
  async with api.LiveKitAPI() as livekit_api:
    transfer_to = 'tel:+12402123203'

    try:
      await livekit_api.sip.transfer_sip_participant(
          api.TransferSIPParticipantRequest(
              participant_identity=participant_identity,
              room_name=room_name,
              transfer_to=transfer_to,
              play_dialtone=False,
          )
      )
      print("SIP participant transferred successfully")
    except api.SipCallError as error:
      print(f"SIP error code: {error.sip_status_code}")
      print(f"SIP error message: {error.sip_status}")
    except api.ServerError as error:
      print(f"Error transferring SIP participant: {error.code} - {error.message}")

class ListenAndRespondAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
                You are the first agent. Please always remind the user of this when you talk to them
            """
        )

    async def on_enter(self):
        
        self.session.generate_reply()
        my_logger.info(f"before sleep {self.session.room_io.room.num_participants} participants")

        await sleep(10)

        participants = self.session.room_io.room.remote_participants

        
        my_logger.info(f"{self.session.room_io.room.num_participants} participants")

        
        for key, value in participants.items():
            my_logger.info(f"{key}: {value}")

            await transfer_call(key, self.session.room_io.room.name)

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
# my number +19136605415
# tw number +17248061667
# LK number +12402123203 <- second rule