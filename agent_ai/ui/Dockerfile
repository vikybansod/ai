FROM python:3.13-slim AS builder

WORKDIR /build

COPY requirements.txt . 

RUN pip install --no-cache-dir --user -r requirements.txt


FROM python:3.13-slim AS runner

ARG CHAINLIT_AUTH_SECRET

WORKDIR /ui

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH

COPY app.py ./

EXPOSE 8000

CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000", "--headless"]