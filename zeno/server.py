import asyncio
import json
import os
import sys

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from .zeno import Zeno


def run_background_processor(conn, args):
    zeno = Zeno(
        metadata_path=args.metadata[0],
        test_files=args.test_files,
        models=args.models,
        batch_size=args.batch_size,
        id_column=args.id_column,
        data_path=args.data_path,
        cache_path=args.cache_path,
    )

    zeno.start_processing()

    while True:
        case, options = conn.recv()

        if case == "GET_SLICERS":
            slicers = zeno.get_slicers()
            conn.send(
                json.dumps(
                    [
                        {
                            "name": s.name,
                            "source": s.source,
                            "slices": list(s.slices.keys()),
                        }
                        for s in slicers
                    ]
                )
            )

        if case == "GET_TESTERS":
            testers = zeno.get_testers()
            conn.send(
                json.dumps([{"name": s.name, "source": s.source} for s in testers])
            )

        if case == "GET_SLICES":
            slices = zeno.get_slices()
            conn.send(json.dumps([{"name": s.name, "size": s.size} for s in slices]))

        if case == "GET_DATA":
            conn.send(zeno.get_metadata_bytes())

        if case == "GET_SAMPLE":
            conn.send(zeno.get_sample(options))

        if case == "GET_RESULTS":
            res = zeno.get_results()
            res = [
                {
                    "testerName": r.tester_name,
                    "sliceName": r.slice_name,
                    "sliceSize": r.slice_size,
                    "modelResults": r.model_results,
                }
                for r in res
            ]
            conn.send((zeno.get_status(), json.dumps(res)))


def run_server(conn, args):
    app = FastAPI(title="Frontend API")
    api_app = FastAPI(title="Backend API")

    if args.data_path != "":
        app.mount("/static", StaticFiles(directory=args.data_path), name="static")
    app.mount("/api", api_app)
    app.mount("/", StaticFiles(directory="./frontend", html=True), name="base")

    @api_app.get("/slicers")
    def get_slicers():
        conn.send(("GET_SLICERS", ""))
        return conn.recv()

    @api_app.get("/slices")
    def get_slices():
        conn.send(("GET_SLICES", ""))
        return conn.recv()

    @api_app.get("/sample/{sli}")
    def get_sample(sli):
        conn.send(("GET_SAMPLE", sli))
        return Response(content=conn.recv())

    @api_app.get("/testers")
    def get_testers():
        conn.send(("GET_TESTERS", ""))
        return conn.recv()

    @api_app.get("/data")
    def get_data():
        conn.send(("GET_DATA", ""))
        return Response(content=conn.recv())

    @api_app.websocket("/results")
    async def results_websocket(websocket: WebSocket):
        await websocket.accept()
        previous_status = ""
        while True:
            await asyncio.sleep(0.5)
            conn.send(("GET_RESULTS", ""))
            res = conn.recv()
            if res[1] != previous_status:
                print("status: ", res[0])
                previous_status = res[1]
                await websocket.send_json({"status": res[0], "results": res[1]})

    uvicorn.run(app, host="localhost", port=8000)
