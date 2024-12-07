import asyncio
from pipecat.pipeline.pipeline import Pipeline
from pipecat.services.openai import OpenAILLMService
from pipecat.transports.services.daily import DailyTransport, DailyParams
from pipecat.vad.silero import SileroVADAnalyzer
from pipecat.services.elevenlabs import ElevenLabsTTSService
from pipecat.pipeline.runner import PipelineRunner
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.openai import OpenAILLMService
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.frameworks.rtvi import (
    RTVIBotTranscriptionProcessor,
    RTVIUserTranscriptionProcessor,
)
from pipecat.frames.frames import (
    EndFrame,
    LLMMessagesFrame,
)
import os

async def main(room_url, token, character_name, personality):
    print("I AM ALIVE")
    # Define transport
    transport = DailyTransport(
        room_url, token, character_name, DailyParams(                
            audio_out_enabled=True,
                camera_out_enabled=False,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
                transcription_enabled=True,)
    )

    # Define services
    llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")
    tts = ElevenLabsTTSService(api_key=os.getenv("ELEVENLABS_API_KEY"), voice_id=os.getenv("ELEVENLABS_VOICE_ID"))

    # Messages and pipeline
    messages = [{"role": "system", "content": f"You are {character_name}. {personality}"}]
    rtvi_user_transcription = RTVIUserTranscriptionProcessor()

        # This will emit BotTranscript events.
    rtvi_bot_transcription = RTVIBotTranscriptionProcessor()

    context = OpenAILLMContext(messages)
    context_aggregator = llm.create_context_aggregator(context)

    pipeline = Pipeline(
            [
                transport.input(),
                rtvi_user_transcription,
                context_aggregator.user(),
                llm,
                rtvi_bot_transcription,
                tts,
                transport.output(),
                context_aggregator.assistant(),
            ]
        )

    # Run bot
    task = PipelineTask(pipeline, PipelineParams(allow_interruptions=True))

    @transport.event_handler("on_first_participant_joined")
    async def on_first_participant_joined(transport, participant):
        await transport.capture_participant_transcription(participant["id"])
        await task.queue_frames([LLMMessagesFrame(messages)])

    @transport.event_handler("on_participant_left")
    async def on_participant_left(transport, participant, reason):
        print(f"Participant left: {participant}")
        await task.queue_frame(EndFrame())


    # await task.queue_frame(quiet_frame)
    runner = PipelineRunner()

    await runner.run(task)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pipecat Bot")
    parser.add_argument("--room_url", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--character_name", required=True)
    parser.add_argument("--personality", required=True)
    args = parser.parse_args()

    asyncio.run(main(args.room_url, args.token, args.character_name, args.personality))
