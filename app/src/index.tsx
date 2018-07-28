import * as React from 'react';
import * as ReactDOM from 'react-dom';
import App from './App';
import './index.css';

const appState = {
  avatars: [
    { name: "embiid", state: { sensors: { time: 100, values: [] }, setpoints: { time: 200, values: [] } } }
  ]
}

ReactDOM.render(
  <App avatars={appState.avatars} />,
  document.getElementById('root') as HTMLElement
);
