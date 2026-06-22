import time
import redis
from fastapi import FastAPI, Request, HTTPException, Response, status
from fastapi.responses import JSONResponse
import redis.asyncio as aioredis


app = FastAPI(title ="Rate Limiter API")

#Initialize Redis connection
redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)
#Connect to local instance of Redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

LIMIT = 5  # Maximum number of requests allowed
WINDOW_SIZE = 60  # Time window in seconds

@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    #1. Get the client's IP address
    client_ip = request.client.host

    #2. Generate the unique fixed window key based on the client's IP address and the current time window
    current_window = int(time.time() // WINDOW_SIZE)
    window_key = f"rl:{client_ip}:{current_window}"

    try:   
        #3. Increment the request count for the current window
        request_count = await redis_client.incr(window_key)

        #4. Set the expiration time for the key if it's a new key
        if request_count == 1:
            await redis_client.expire(window_key, WINDOW_SIZE)

        #5. Calculate the remaining requests allowed in the current window
        time_to_live = await redis_client.ttl(window_key)
        remaining_requests = max(0, LIMIT - request_count)

        #6. If the request count exceeds the limit, return a 429 Too Many Requests response
        if request_count > LIMIT:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Try again later.",
                    "remaining_requests": remaining_requests,
                    "time_to_reset": time_to_live
                }
            )
    except Exception as e:
        print(f"Error occurred: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An error occurred while processing the request."}
        )

    #7. If the request count is within the limit, proceed with the request
    response: Response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(LIMIT)
    response.headers["X-RateLimit-Remaining"] = str(remaining_requests)
    return response

# -- Example endpoint to test the rate limiter
@app.get("/")
async def home():
    return {"message": "Welcome to the Rate Limiter API!"}

@app.get("/data")
async def get_data():
    return {"message": "Here is some data!"}
