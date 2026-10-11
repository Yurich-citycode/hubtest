import { Composition } from 'remotion';
import { TitleOutro } from './TitleOutro';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="TitleOutro"
        component={TitleOutro}
        durationInFrames={120}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
