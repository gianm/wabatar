import * as React from 'react';
import './App.css';

export interface AppState {
  avatars: Avatar[];
}

export interface Avatar {
  name: string;
  state: AvatarState;
}

export interface AvatarState {
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
      rows.push(<tr><td>{avatar.name}</td></tr>)
    }

    return (
      <div className="App">
        <header className="App-header">
          <h1 className="App-title">WABATAR</h1>
        </header>
        <table className="avatars">
          <tr>
            <th>Avatar</th>
          </tr>
          {rows}
        </table>
      </div>
    );
  }
}

export default App;
