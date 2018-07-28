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
import './App.css';

const IDX_TEMPERATURE = 0
const IDX_CO2 = 2
const IDX_O2 = 3
const IDX_PRESSURE = 4
const IDX_RH = 5

export interface AppState {
  avatars: AvatarState[];
}

export interface AvatarState {
  name: string;
  sensors: Readouts;
  setpoints: Readouts;
}

export interface Readouts {
  time: number;
  values: number[];
}

class App extends React.Component<AppState, object> {
  public render() {
    const { avatars = [] } = this.props;
    const rows: JSX.Element[] = [];

    for (const avatar of avatars) {
      rows.push(
        <tr>
          <td>{avatar.name}</td>
          <td>{avatar.sensors.values[IDX_TEMPERATURE]}</td>
          <td>{avatar.sensors.values[IDX_CO2]}</td>
          <td>{avatar.sensors.values[IDX_O2]}</td>
          <td>{avatar.sensors.values[IDX_PRESSURE]}</td>
          <td>{avatar.sensors.values[IDX_RH]}</td>
          <td>{avatar.sensors.time}</td>
        </tr>
      )
    }

    return (
      <div className="App">
        <header className="App-header">
          <h1 className="App-title">WABATAR</h1>
        </header>
        <table className="avatars">
          <tr>
            <th>Avatar</th>
            <th>Temperature (&deg;C)</th>
            <th>CO<sub>2</sub></th>
            <th>O<sub>2</sub></th>
            <th>Pressure</th>
            <th>Relative humidity</th>
            <th>Last update</th>
          </tr>
          {rows}
        </table>
      </div>
    );
  }
}

export default App;
