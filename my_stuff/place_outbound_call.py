"""
places an outbound call

```bash
cd my_stuff
lk agent dev place_outbound_call.py
lk room create --name my-room && lk dispatch create --agent-name test-agent --room my-room
```


"""

import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, inference, AgentServer, cli
from livekit.plugins import silero
from livekit import agents, api
import json

load_dotenv()

logger = logging.getLogger("listen-and-respond")
logger.setLevel(logging.INFO)

class ListenAndRespondAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
            """
        )

    # async def on_enter(self):
        
    #     self.session.generate_reply()

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session(agent_name="test-agent")
async def entrypoint(ctx: JobContext):
    logger.info("💚 first")

    ctx.log_context_fields = {"room": ctx.room.name}
    logger.info("💚 second")

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    logger.info("💚 third")
    agent = ListenAndRespondAgent()
    logger.info("💚 fourth")

    await session.start(agent=agent, room=ctx.room)
    logger.info("💚 fifth")
    await ctx.connect()

    logger.info("💚 sixth")

    phone_number = "+19136605415"
    # phone_number = "+17248061667"

    # The participant's identity can be anything you want, but this example uses the phone number itself
    sip_participant_identity = phone_number
    if phone_number is not None:
        logger.info("💚 seventh")
        # The outbound call will be placed after this method is executed
        try:
            logger.info("💚 8")
            logger.info(f"💚 {ctx.room.name} ")
            await ctx.api.sip.create_sip_participant(api.CreateSIPParticipantRequest(
                # This ensures the participant joins the correct room
                room_name=ctx.room.name,

                # This is the outbound trunk ID to use
                # You can get this from LiveKit CLI with `lk sip outbound list`
                sip_trunk_id='ST_EfLWk22seka5',
                sip_number="+17248061667",

                # The outbound phone number to dial and identity to use
                sip_call_to=phone_number,
                participant_identity=sip_participant_identity,

                # This waits until the call is answered before returning
                wait_until_answered=True,
                
            ))
            logger.info("💚 9")
            print("call picked up successfully")
        except api.SipCallError as e:
            # sip_status_code / sip_status carry the status from the upstream carrier
            logger.info("💚 10")
            logger.info(f"call failed: {e.sip_status_code} {e.sip_status}")
            ctx.shutdown()
            return

    # Wait for the SIP participant to fully join the room before starting the session
    logger.info("💚 beginning waiting for participant")
    participant = await ctx.wait_for_participant(identity=sip_participant_identity)

    # Create and start your AgentSession
    # session = AgentSession(...)
    # await session.start(room=ctx.room, participant=participant, agent=Assistant(), ...)


if __name__ == "__main__":
    cli.run_app(server)

