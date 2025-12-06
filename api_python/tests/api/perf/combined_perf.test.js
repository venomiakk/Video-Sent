const axios = require("axios");
const { MongoClient, ObjectId } = require("mongodb");

// Increase timeout because transcription/analysis may take several minutes
jest.setTimeout(10 * 60 * 1000);

const BASE_URL = process.env.BASE_URL || "http://localhost:8000";
const TEST_TOKEN = process.env.TEST_TOKEN || "";
const TEST_VIDEO_URL =
  process.env.TEST_VIDEO_URL || "https://www.youtube.com/watch?v=1nQ8xKk5Yiw";
const MONGO_URI = process.env.MONGO_URI || "mongodb://localhost:27017";
const MONGO_DB = process.env.MONGO_DB || "video_sentiment";

function authHeader() {
  return TEST_TOKEN ? { Authorization: `Bearer ${TEST_TOKEN}` } : {};
}

describe("Transcription -> Analysis performance flow", () => {
  test("creates transcription, runs analysis, then cleans up DB", async () => {
    const headers = { "Content-Type": "application/json", ...authHeader() };

    // 1) Transcription
    const trPayload = { url: TEST_VIDEO_URL, model: "deepgram-nova-2" };
    const trStart = Date.now();
    const trRes = await axios.post(
      `${BASE_URL}/api/v1/transcribe/process`,
      trPayload,
      { headers }
    );
    const trEnd = Date.now();
    const transcriptionDurationMs = trEnd - trStart;

    const trData = trRes.data || {};
    const transcriptionId =
      trData._id || trData.id || (trData.id && trData.id.$oid) || null;

    console.log("Transcription response data:", trData);
    console.log(`Transcription time: ${transcriptionDurationMs} ms`);

    expect(transcriptionId).toBeTruthy();

    // 2) Analysis
    const analyzeStart = Date.now();
    const anRes = await axios.post(
      `${BASE_URL}/api/v1/sentiment/analyze/${transcriptionId}`,
      null,
      { headers }
    );
    const analyzeEnd = Date.now();
    const analysisDurationMs = analyzeEnd - analyzeStart;

    const analysisData =
      anRes.data && anRes.data.message ? anRes.data.message : anRes.data;
    console.log("Analysis response data:", analysisData);
    console.log(`Analysis time: ${analysisDurationMs} ms`);

    expect(analysisData).toBeTruthy();

    // 3) Cleanup in Mongo (optional, only if MONGO_URI provided)
    if (MONGO_URI) {
      // Modern MongoDB Node driver ignores the legacy options; create client without them.
      const client = new MongoClient(MONGO_URI);
      try {
        await client.connect();
        const db = client.db(MONGO_DB);

        // Delete sentiment analysis documents for this transcription
        const saResult = await db
          .collection("sentiment_analysis")
          .deleteMany({ transcription_id: String(transcriptionId) });
        console.log(
          `Deleted ${saResult.deletedCount} sentiment_analysis documents for transcription ${transcriptionId}`
        );

        // Delete transcription document (if ObjectId format)
        let deletedTrans = { deletedCount: 0 };
        try {
          const oid = new ObjectId(String(transcriptionId));
          deletedTrans = await db
            .collection("transcriptions")
            .deleteOne({ _id: oid });
        } catch (e) {
          // transcriptionId not an ObjectId — try deleting by string _id or link_hash
          deletedTrans = await db.collection("transcriptions").deleteMany({
            $or: [{ _id: transcriptionId }, { link_hash: transcriptionId }],
          });
        }
        console.log(
          `Deleted transcription docs count: ${deletedTrans.deletedCount}`
        );
      } finally {
        await client.close();
      }
    } else {
      console.log(
        "MONGO_URI not provided — skipping DB cleanup. Set MONGO_URI to enable automatic cleanup."
      );
    }

    // Print summary
    console.log("---- PERF SUMMARY ----");
    console.log(`Transcription ID: ${transcriptionId}`);
    console.log(`Transcription time (ms): ${transcriptionDurationMs}`);
    console.log(`Analysis time (ms): ${analysisDurationMs}`);
  });
});
