/*
 * Copyright 2018 Gian Merlino
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import * as React from 'react';
import * as ReactDOM from 'react-dom';
import App from './App';
// import { AvatarState } from './App';
import './index.css';

/*
const avatars: AvatarState[] = [
  {
    name: "embiid",
    sensors: {time: 1532804226.3726523, values: [28.7, 0.0, 0.0, 12.3, 0.0, 36.2]},
    setpoints: {time: 1532804223.8133285, values: [32.0, 0, 0.0, 9.9, 0.1, 0]}
  }
]
*/

function tick() {
  fetch("http://192.168.0.127:8080/v1/status")
    .then(result => result.json())
    .then(
      (result) => {
        ReactDOM.render(
          <App avatars={result} />,
          document.getElementById('root') as HTMLElement
        );
      },
      (error) => {
        // console.log("Oops!! " + error);
      }
    )
}

setInterval(tick, 1000);
