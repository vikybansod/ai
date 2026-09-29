FROM python:3.14-slim AS builder

WORKDIR /build

COPY requirements.txt . 

RUN pip install --no-cache-dir --user -r requirements.txt


FROM python:3.14-slim AS runner

ARG OPENAI_ADMIN_KEY

WORKDIR /agent

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH

COPY ./strands/agent.py agent.py

CMD [ "python", "agent.py" ]