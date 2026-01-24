const HOST = window.location.hostname;
const API_PORT = '8000';

export const API_BASE_URL = `http://${HOST}:${API_PORT}`;
export const WS_BASE_URL = `ws://${HOST}:${API_PORT}`; 

export const getVideoStreamUrl = (): string => {
    return  `${API_BASE_URL}/video_feed`;
}; 

export const createWebSocketConnection = (): WebSocket => {
    return new WebSocket(`${WS_BASE_URL}/ws`);
};
